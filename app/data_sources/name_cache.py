from __future__ import annotations

import json
from pathlib import Path

import akshare as ak


ROOT_DIR = Path(__file__).resolve().parents[2]
CACHE_PATH = ROOT_DIR / "data" / "stock_names.json"


def get_stock_name(code: str) -> str:
    normalized = _normalize_code(code)
    cache = _load_cache()
    cached_name = cache.get(normalized)
    if cached_name and cached_name != normalized:
        return cached_name

    name = _fetch_name(normalized)
    if name:
        cache[normalized] = name
        _save_cache(cache)
        return name

    return normalized


def _fetch_name(code: str) -> str | None:
    for fetcher in (_fetch_name_from_baostock, _fetch_name_from_akshare_spot, _fetch_name_from_akshare_info):
        name = fetcher(code)
        if name and name != code:
            return name
    return None


def _fetch_name_from_akshare_spot(code: str) -> str | None:
    try:
        spot = ak.stock_zh_a_spot_em()
        if "代码" not in spot.columns or "名称" not in spot.columns:
            return None
        row = spot.loc[spot["代码"].astype(str).str.zfill(6) == code.zfill(6)]
        if row.empty:
            return None
        return _clean_name(row.iloc[0]["名称"])
    except Exception:
        return None


def _fetch_name_from_akshare_info(code: str) -> str | None:
    try:
        info = ak.stock_individual_info_em(symbol=code)
        if "item" not in info.columns or "value" not in info.columns:
            return None
        item_col = info["item"].astype(str)
        row = info.loc[item_col.isin(["股票简称", "股票名称", "名称"])]
        if row.empty:
            return None
        return _clean_name(row.iloc[0]["value"])
    except Exception:
        return None


def _fetch_name_from_baostock(code: str) -> str | None:
    try:
        import baostock as bs
    except ImportError:
        return None

    login_result = bs.login()
    try:
        if getattr(login_result, "error_code", "0") != "0":
            return None
        rs = bs.query_stock_basic(code=_to_baostock_code(code))
        if getattr(rs, "error_code", "0") != "0":
            return None
        rows = []
        while rs.next():
            rows.append(rs.get_row_data())
        if not rows:
            return None
        fields = list(rs.fields)
        name_index = fields.index("code_name") if "code_name" in fields else 1
        return _clean_name(rows[0][name_index])
    except Exception:
        return None
    finally:
        try:
            bs.logout()
        except Exception:
            pass


def _clean_name(value) -> str | None:
    name = str(value).strip()
    if not name or name.lower() == "nan":
        return None
    return name


def _normalize_code(code: str) -> str:
    text = code.strip().lower()
    if text.startswith(("sh.", "sz.", "bj.")):
        return text[3:]
    if text.startswith(("sh", "sz", "bj")):
        return text[2:]
    return text


def _to_baostock_code(code: str) -> str:
    normalized = _normalize_code(code)
    if normalized.startswith(("6", "9")):
        return f"sh.{normalized}"
    if normalized.startswith(("8", "4")):
        return f"bj.{normalized}"
    return f"sz.{normalized}"


def _load_cache() -> dict[str, str]:
    if not CACHE_PATH.exists():
        return {}
    try:
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_cache(cache: dict[str, str]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
