"""
data_fetcher.py (robust)
- Avoids passing requests.Session to yfinance
- Validates/adjusts dates (no future end_date)
- Robust normalization (no KeyError: 'date')
- Logs previews for debugging
"""

import os
import time
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

import pandas as pd
import yfinance as yf
import requests
from json import JSONDecodeError

# optional fallback
try:
    from yahooquery import Ticker as YQTicker  # type: ignore
    _HAS_YAHOOQUERY = True
except Exception:
    _HAS_YAHOOQUERY = False

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


class DataFetcher:
    NIFTY_50_TICKERS = [
        "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
        "HINDUNILVR.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS",
        "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "SUNPHARMA.NS",
        "TITAN.NS", "BAJFINANCE.NS", "ULTRACEMCO.NS", "NESTLEIND.NS", "WIPRO.NS",
        "HCLTECH.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "TATAMOTORS.NS",
        "BAJAJFINSV.NS", "M&M.NS", "TECHM.NS", "ADANIPORTS.NS", "COALINDIA.NS",
        "TATASTEEL.NS", "HINDALCO.NS", "JSWSTEEL.NS", "INDUSINDBK.NS", "DRREDDY.NS",
        "CIPLA.NS", "APOLLOHOSP.NS", "DIVISLAB.NS", "EICHERMOT.NS", "HEROMOTOCO.NS",
        "GRASIM.NS", "BRITANNIA.NS", "SHREECEM.NS", "TATACONSUM.NS", "BPCL.NS",
        "UPL.NS", "ADANIENT.NS", "BAJAJ-AUTO.NS", "SBILIFE.NS", "HDFCLIFE.NS"
    ]

    NIFTY_100_ADDITIONAL = [
        "PIDILITIND.NS", "BERGEPAINT.NS", "HAVELLS.NS", "DABUR.NS", "GODREJCP.NS",
        "MARICO.NS", "COLPAL.NS", "TORNTPHARM.NS", "BANDHANBNK.NS", "INDIGO.NS",
        "SIEMENS.NS", "DLF.NS", "GAIL.NS", "AMBUJACEM.NS", "ACC.NS",
        "BOSCHLTD.NS", "VEDL.NS", "ADANIGREEN.NS", "ADANITRANS.NS", "MOTHERSON.NS",
        "TATAPOWER.NS", "PNB.NS", "BANKBARODA.NS", "IOCL.NS", "LUPIN.NS",
        "BIOCON.NS", "ICICIPRULI.NS", "SBICARD.NS", "MUTHOOTFIN.NS", "PFC.NS",
        "RECLTD.NS", "JINDALSTEL.NS", "SAIL.NS", "NMDC.NS", "CONCOR.NS",
        "LAURUSLABS.NS", "AUROPHARMA.NS", "ALKEM.NS", "DMART.NS", "PAGEIND.NS",
        "ABCAPITAL.NS", "L&TFH.NS", "CHOLAFIN.NS", "LICHSGFIN.NS", "MPHASIS.NS",
        "PERSISTENT.NS", "COFORGE.NS", "LTIM.NS", "TATAELXSI.NS", "OFSS.NS"
    ]

    INDICES = ["^NSEI", "^BSESN", "^NSEBANK", "^CNXMIDCAP"]

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def get_all_tickers(self) -> List[str]:
        return list(dict.fromkeys(
            self.NIFTY_50_TICKERS +
            self.NIFTY_100_ADDITIONAL +
            self.INDICES
        ))


    @staticmethod
    def _ensure_dates_valid(start_date: str, end_date: str) -> Tuple[str, str]:
        today = datetime.now(timezone.utc).date()
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d").date()
        except Exception:
            sd = today - timedelta(days=60)
        try:
            ed = datetime.strptime(end_date, "%Y-%m-%d").date()
        except Exception:
            ed = today
        if ed > today:
            logger.info("end_date in future; adjusting to today.")
            ed = today
        if sd >= ed:
            logger.info("start_date >= end_date; adjusting start to 90 days before end.")
            sd = ed - timedelta(days=90)
        return sd.strftime("%Y-%m-%d"), ed.strftime("%Y-%m-%d")

    @staticmethod
    def _find_date_column(df: pd.DataFrame) -> Optional[str]:
        # 1) If index is datetime-like, reset_index will create the date col; index name might be 'Date' or 'date'
        # 2) Look for any column name containing 'date'
        # 3) Look for columns with datetime dtype
        # 4) Fallback to the first column
        # Return column name (after reset_index), or None if not found
        # NOTE: call this after df.reset_index()
        # Check direct 'date' match
        for col in df.columns:
            if str(col).lower() == "date":
                return col
        # substring match
        for col in df.columns:
            if "date" in str(col).lower():
                return col
        # dtype datetime-like
        for col in df.columns:
            try:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    return col
            except Exception:
                continue
        # fallback: first column (often reset_index creates the date as first col)
        if len(df.columns) > 0:
            return df.columns[0]
        return None

    @staticmethod
    def _sanitize_df(df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names and ensure a 'date' column exists and is formatted."""
        # If MultiIndex columns (download may produce multi-index), flatten
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        # If index is not a range, keep it by resetting index
        df = df.reset_index()
        # lowercase and replace spaces
        df.columns = [str(c).lower().replace(" ", "_") for c in df.columns]

        # find which column is date
        date_col = DataFetcher._find_date_column(df)
        if date_col is None:
            # nothing sensible found; log and raise a controlled error
            logger.warning("Unable to detect a date-like column in fetched DataFrame. Columns: %s", list(df.columns))
            # create a synthetic date column from the index position - but safer to raise to trigger retry
            raise KeyError("date")

        # rename found column to 'date' if necessary
        if date_col != "date":
            df = df.rename(columns={date_col: "date"})

        # convert to datetime and format
        try:
            df["date"] = pd.to_datetime(df["date"])
            df["date"] = df["date"].dt.strftime("%Y-%m-%d")
        except Exception as e:
            logger.warning("Failed to parse date column '%s': %s", date_col, e)
            raise

        # normalize column names again (already lowercased above)
        df.columns = [str(c).lower().replace(" ", "_") for c in df.columns]
        return df

    def _yahooquery_fetch(self, ticker: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        if not _HAS_YAHOOQUERY:
            return None
        try:
            logger.info("Trying yahooquery fallback for %s", ticker)
            yq = YQTicker(ticker)
            df = yq.history(start=start_date, end=end_date)
            if df is None or df.empty:
                return None
            # yahooquery sometimes returns index with ticker as first level
            if isinstance(df.index, pd.MultiIndex):
                df = df.reset_index()
            df = self._sanitize_df(df)
            return df
        except Exception as e:
            logger.debug("yahooquery fallback failed: %s", e)
            return None

    def fetch_data(self, ticker: str, start_date: str, end_date: str, retries: int = 3, min_rows: int = 40) -> Optional[pd.DataFrame]:
        start_date, end_date = self._ensure_dates_valid(start_date, end_date)

        for attempt in range(retries):
            try:
                logger.info(f"Fetching {ticker} (attempt {attempt + 1}/{retries})")

                # diagnostic probe (do NOT pass this session to yfinance)
                probe_url = f"https://finance.yahoo.com/quote/{ticker}"
                try:
                    probe_resp = requests.get(probe_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=7)
                    if probe_resp.status_code >= 400:
                        logger.warning("Yahoo returned HTTP %d for probe of %s", probe_resp.status_code, ticker)
                except Exception as e:
                    logger.debug("Probe request failed: %s", e)

                # Use yfinance without custom session
                stock = yf.Ticker(ticker)
                df = None
                try:
                    df = stock.history(start=start_date, end=end_date, auto_adjust=False, actions=False)
                except Exception as e:
                    logger.debug("yfinance.history() raised: %s", e)
                    df = None

                # fallback to yf.download()
                if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                    try:
                        logger.info("history() empty; trying yf.download() for %s", ticker)
                        df = yf.download(ticker, start=start_date, end=end_date, progress=False, auto_adjust=False, threads=False)
                    except Exception as e:
                        logger.debug("yf.download error: %s", e)
                        df = None

                # fallback to yahooquery if enabled
                if (df is None or (isinstance(df, pd.DataFrame) and df.empty)) and _HAS_YAHOOQUERY:
                    df = self._yahooquery_fetch(ticker, start_date, end_date)

                # if still empty
                if df is None or (isinstance(df, pd.DataFrame) and df.empty):
                    logger.warning("No data returned for %s on attempt %d", ticker, attempt + 1)
                    wait = min(30, (2 ** attempt))
                    logger.info("Waiting %ds before next attempt...", wait)
                    time.sleep(wait)
                    continue

                # At this point df is non-empty. Log its preview so we can debug shapes.
                try:
                    logger.info("Fetched raw DataFrame for %s: shape=%s; columns=%s", ticker, getattr(df, "shape", None), list(df.columns))
                    # show small preview
                    preview = df.head(3)
                    logger.debug("Data preview:\n%s", preview.to_string())
                except Exception:
                    logger.debug("Could not log preview of fetched df.")

                # sanitize and normalize
                df = self._sanitize_df(df)

                # validate rows
                if len(df) < min_rows:
                    logger.warning("Insufficient rows for %s: %d rows (need >= %d)", ticker, len(df), min_rows)
                    wait = min(30, (attempt + 1) * 3)
                    logger.info("Waiting %ds before next attempt...", wait)
                    time.sleep(wait)
                    continue

                # save
                filename = os.path.join(self.data_dir, f"{ticker.replace('^', 'INDEX_')}.csv")
                df.to_csv(filename, index=False)
                logger.info("Saved %s (%d rows) to %s", ticker, len(df), filename)
                return df

            except KeyError as ke:
                # This is likely from date detection failure; log and retry after backoff
                logger.error("Key error while processing %s: %s", ticker, ke)
                wait = min(30, (attempt + 1) * 5)
                logger.info("Waiting %ds before retrying after KeyError...", wait)
                time.sleep(wait)
                continue
            except JSONDecodeError as jde:
                logger.error("JSON decode error for %s: %s", ticker, jde)
                wait = min(30, (attempt + 1) * 5)
                logger.info("Waiting %ds before retrying after JSON error...", wait)
                time.sleep(wait)
                continue
            except Exception as exc:
                logger.error("Error fetching %s: %s", ticker, exc)
                logger.debug("Exception info:", exc_info=True)
                if attempt < retries - 1:
                    wait_time = min(30, (attempt + 1) * 5)
                    logger.info("Waiting %ds before retry...", wait_time)
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error("Failed to fetch %s after %d attempts", ticker, retries)
                    return None

        return None

    def fetch_all(self, months: int = 2) -> dict:
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=months * 30)
        start_s = start_date.strftime("%Y-%m-%d")
        end_s = end_date.strftime("%Y-%m-%d")
        logger.info("Fetching data from %s to %s", start_s, end_s)
        tickers = self.get_all_tickers()
        results = {"success": 0, "failed": 0, "failed_tickers": []}
        for t in tickers:
            df = self.fetch_data(t, start_s, end_s)
            if df is not None:
                results["success"] += 1
            else:
                results["failed"] += 1
                results["failed_tickers"].append(t)
            time.sleep(1)
        logger.info("Completed: %d success, %d failed", results["success"], results["failed"])
        return results

    def load_data(self, ticker: str) -> Optional[pd.DataFrame]:
        filename = os.path.join(self.data_dir, f"{ticker.replace('^', 'INDEX_')}.csv")
        if not os.path.exists(filename):
            logger.warning("File not found: %s", filename)
            return None
        try:
            df = pd.read_csv(filename)
            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"])
            return df
        except Exception as e:
            logger.error("Error loading %s: %s", ticker, e)
            return None


if __name__ == "__main__":
    fetcher = DataFetcher()
    result = fetcher.fetch_all(months=2)
    print(result)


# if __name__ == "__main__":
    fetcher = DataFetcher()
    print("\n=== Testing Single Stock Fetch ===")
    end = datetime.now(timezone.utc).date()
    start = end - timedelta(days=90)
    df = fetcher.fetch_data("RELIANCE.NS", start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"), retries=3)
    if df is not None:
        print("✓ Successfully fetched RELIANCE.NS")
        print("Shape:", df.shape)
        print("Columns:", list(df.columns))
        print("Date range:", df["date"].min(), "to", df["date"].max())
        print(df.head(3))
    else:
        print("✗ Failed to fetch RELIANCE.NS")

    print("\n=== Testing Data Loading ===")
    loaded = fetcher.load_data("RELIANCE.NS")
    if loaded is not None:
        print("✓ Loaded from disk:", loaded.shape)
    else:
        print("✗ No saved CSV found or failed to load.")
