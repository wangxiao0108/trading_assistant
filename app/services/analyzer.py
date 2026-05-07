from __future__ import annotations

import json
from dataclasses import dataclass

from app.data_sources.akshare_source import fetch_daily
from app.rules.indicators import add_moving_averages
from app.rules.rule_engine import RuleResult, analyze_rules


@dataclass
class AnalysisResult:
    code: str
    name: str
    source: str
    fetched_at: str
    kline_date: str
    latest_close: float
    latest_pct_chg: float | None
    ma5: float
    ma13: float
    ma20: float
    chart_json: str
    data_notes: list[str]
    market_notes: list[str]
    rule_result: RuleResult


def analyze_stock(code: str) -> AnalysisResult:
    daily = fetch_daily(code)
    df = add_moving_averages(daily.df)
    latest = df.iloc[-1]
    rule_result = analyze_rules(df)
    chart_json = _build_chart_json(df)

    return AnalysisResult(
        code=daily.code,
        name=daily.name,
        source=daily.source,
        fetched_at=daily.fetched_at.strftime("%Y-%m-%d %H:%M:%S"),
        kline_date=latest["date"].strftime("%Y-%m-%d"),
        latest_close=float(latest["close"]),
        latest_pct_chg=None if latest.get("pct_chg") is None else float(latest["pct_chg"]),
        ma5=float(latest["ma5"]),
        ma13=float(latest["ma13"]),
        ma20=float(latest["ma20"]),
        chart_json=chart_json,
        data_notes=[
            f"当前本次分析使用 {daily.source}。",
            "当前版本只做日线级规则分析，暂未接入分时、盘口、资金流。",
            "免费公开数据可能存在延迟、接口变动或拉取失败。",
        ],
        market_notes=[
            "大盘环境：第一版暂未接入指数规则判断。",
            "板块强弱：第一版暂未接入行业/概念强弱判断。",
            "系统仓位倾向：需要大盘和板块数据接入后再给出。",
        ],
        rule_result=rule_result,
    )


def _build_chart_json(df) -> str:
    view = df.tail(60).copy()
    rows = []
    for _, row in view.iterrows():
        rows.append(
            {
                "date": row["date"].strftime("%m-%d"),
                "open": _clean_float(row["open"]),
                "close": _clean_float(row["close"]),
                "high": _clean_float(row["high"]),
                "low": _clean_float(row["low"]),
                "volume": _clean_float(row["volume"]),
                "ma5": _clean_float(row["ma5"]),
                "ma13": _clean_float(row["ma13"]),
                "ma20": _clean_float(row["ma20"]),
            }
        )
    return json.dumps(rows, ensure_ascii=False)


def _clean_float(value) -> float | None:
    try:
        if value != value:
            return None
        return round(float(value), 4)
    except (TypeError, ValueError):
        return None
