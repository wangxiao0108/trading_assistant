from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
import os

import akshare as ak
import pandas as pd

from app.data_sources.name_cache import get_stock_name


@dataclass
class StockDailyData:
    code: str
    name: str
    source: str
    fetched_at: datetime
    df: pd.DataFrame


class DataSourceError(RuntimeError):
    pass


def fetch_daily(code: str, days: int = 120) -> StockDailyData:
    normalized = normalize_code(code)
    errors: list[Exception] = []

    try:
        return _fetch_baostock_daily(normalized, days)
    except Exception as exc:
        errors.append(exc)

    try:
        raw = _fetch_akshare_daily(normalized)
        if raw.empty:
            raise DataSourceError(f"AKShare 未获取到 {code} 的日 K 数据。")
        df = _normalize_akshare_df(raw, days)
        name = get_stock_name(normalized)
        return StockDailyData(code=normalized, name=name, source="AKShare/东方财富", fetched_at=datetime.now(), df=df)
    except Exception as exc:
        errors.append(exc)

    raise _make_data_source_error(errors) from errors[-1]


def _normalize_akshare_df(raw: pd.DataFrame, days: int) -> pd.DataFrame:
    df = raw.rename(
        columns={
            "日期": "date",
            "股票代码": "code",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount",
            "振幅": "amplitude",
            "涨跌幅": "pct_chg",
            "涨跌额": "change",
            "换手率": "turnover",
        }
    )
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    numeric_columns = ["open", "close", "high", "low", "volume", "amount", "amplitude", "pct_chg", "change", "turnover"]
    for column in numeric_columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df.sort_values("date").tail(days).reset_index(drop=True)


def _fetch_akshare_daily(code: str) -> pd.DataFrame:
    try:
        return ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            adjust="qfq",
        )
    except Exception as first_exc:
        if not _looks_like_proxy_error(first_exc):
            raise
        with _without_proxy_env():
            try:
                return ak.stock_zh_a_hist(
                    symbol=code,
                    period="daily",
                    adjust="qfq",
                )
            except Exception:
                raise first_exc


def _fetch_baostock_daily(code: str, days: int) -> StockDailyData:
    try:
        import baostock as bs
    except ImportError as exc:
        raise DataSourceError("BaoStock 未安装：请先运行 pip install -r requirements.txt。") from exc

    bs_code = to_baostock_code(code)
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=max(days * 3, 240))).strftime("%Y-%m-%d")
    fields = "date,code,open,high,low,close,preclose,volume,amount,turn,pctChg,isST"

    login_result = bs.login()
    try:
        if getattr(login_result, "error_code", "0") != "0":
            raise DataSourceError(f"BaoStock 登录失败：{getattr(login_result, 'error_msg', '')}")
        rs = bs.query_history_k_data_plus(
            bs_code,
            fields,
            start_date=start_date,
            end_date=end_date,
            frequency="d",
            adjustflag="2",
        )
        if getattr(rs, "error_code", "0") != "0":
            raise DataSourceError(f"BaoStock 数据获取失败：{getattr(rs, 'error_msg', '')}")
        rows = []
        while rs.next():
            rows.append(rs.get_row_data())
        raw = pd.DataFrame(rows, columns=rs.fields)
    finally:
        bs.logout()

    if raw.empty:
        raise DataSourceError(f"BaoStock 未获取到 {code} 的日 K 数据。")

    df = _normalize_baostock_df(raw, days)
    name = get_stock_name(code)
    return StockDailyData(code=code, name=name, source="BaoStock 前复权日 K", fetched_at=datetime.now(), df=df)


def _normalize_baostock_df(raw: pd.DataFrame, days: int) -> pd.DataFrame:
    df = raw.rename(
        columns={
            "pctChg": "pct_chg",
            "turn": "turnover",
        }
    )
    df["date"] = pd.to_datetime(df["date"])
    df["change"] = pd.to_numeric(df["close"], errors="coerce") - pd.to_numeric(df["preclose"], errors="coerce")
    df["amplitude"] = None
    numeric_columns = ["open", "close", "high", "low", "volume", "amount", "pct_chg", "change", "turnover", "amplitude"]
    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df.sort_values("date").tail(days).reset_index(drop=True)


def _make_data_source_error(errors: list[Exception]) -> DataSourceError:
    if not errors:
        return DataSourceError("数据源连接失败：未知错误。")

    primary = errors[0]
    fallback_details = "；".join(str(error) for error in errors[1:] if str(error))
    if _looks_like_connection_abort(primary):
        detail = f"备用源也失败：{fallback_details}" if fallback_details else "请检查代理/VPN，或稍后重试。"
        return DataSourceError(f"数据源连接失败：本机代理断开了东方财富接口连接。{detail}")
    message = str(primary)
    if "Max retries exceeded" in message or "HTTPSConnectionPool" in message:
        detail = f"备用源也失败：{fallback_details}" if fallback_details else "请稍后重试。"
        return DataSourceError(f"数据源连接失败：东方财富接口暂时无法访问，{detail}")

    details = "；".join(str(error) for error in errors if str(error))
    return DataSourceError(f"数据源连接失败：{details}")


def _looks_like_proxy_error(exc: Exception) -> bool:
    message = str(exc)
    return _looks_like_connection_abort(exc) or "ProxyError" in message or "Unable to connect to proxy" in message


def _looks_like_connection_abort(exc: Exception) -> bool:
    message = str(exc)
    return (
        "Connection aborted" in message
        or "RemoteDisconnected" in message
        or "Remote end closed connection without response" in message
    )


@contextmanager
def _without_proxy_env():
    proxy_keys = ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]
    old_values = {key: os.environ.get(key) for key in proxy_keys}
    for key in proxy_keys:
        os.environ.pop(key, None)
    try:
        yield
    finally:
        for key, value in old_values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def normalize_code(code: str) -> str:
    text = code.strip().lower()
    if text.startswith(("sh", "sz", "bj")):
        return text[2:]
    return text


def to_baostock_code(code: str) -> str:
    normalized = normalize_code(code)
    if normalized.startswith(("6", "9")):
        return f"sh.{normalized}"
    if normalized.startswith(("8", "4")):
        return f"bj.{normalized}"
    return f"sz.{normalized}"
