from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class RuleCheck:
    name: str
    status: str
    detail: str


@dataclass
class RuleResult:
    conclusion: str
    risk_level: str
    positives: list[str]
    risks: list[str]
    observations: list[str]
    checks: list[RuleCheck]
    action_plan: list[str]


def analyze_rules(df: pd.DataFrame) -> RuleResult:
    if len(df) < 30:
        return RuleResult(
            conclusion="数据不足，暂停判断。",
            risk_level="数据不足",
            positives=[],
            risks=["K线数量不足，无法稳定计算 5/13/20 日线。"],
            observations=[],
            checks=[RuleCheck("K线数量", "数据不足", "K线数量不足，暂停规则判断。")],
            action_plan=["补足 K 线数据后再判断。"],
        )

    latest = df.iloc[-1]
    prev = df.iloc[-2]
    recent_5 = df.tail(5)
    recent_20 = df.tail(20)

    close = float(latest["close"])
    high = float(latest["high"])
    low = float(latest["low"])
    ma5 = float(latest["ma5"])
    ma13 = float(latest["ma13"])
    ma20 = float(latest["ma20"])
    volume = float(latest["volume"])
    vol_ma5 = float(latest["vol_ma5"])
    vol_ma20 = float(latest["vol_ma20"])
    turnover = _safe_float(latest.get("turnover"))
    pct_chg = _safe_float(latest.get("pct_chg"))

    positives: list[str] = []
    risks: list[str] = []
    observations: list[str] = []
    checks: list[RuleCheck] = []

    if close > ma20:
        positives.append("收盘价在 20 日线之上，符合短线基础观察条件。")
        checks.append(RuleCheck("20日线", "通过", "收盘价在 20 日线之上。"))
    else:
        risks.append("收盘价在 20 日线之下，按规则属于谨慎或不做多区域。")
        checks.append(RuleCheck("20日线", "风险", "收盘价在 20 日线之下。"))

    if close > ma5:
        positives.append("收盘价在 5 日线之上，短线走势相对更强。")
        checks.append(RuleCheck("5日线", "通过", "收盘价在 5 日线之上。"))
    else:
        observations.append("收盘价未站上 5 日线，需要继续观察是否重新转强。")
        checks.append(RuleCheck("5日线", "观察", "收盘价未站上 5 日线。"))

    if ma5 > ma13 > ma20:
        positives.append("5/13/20 日线呈多头排列，趋势结构较好。")
        checks.append(RuleCheck("5/13/20结构", "通过", "均线呈多头排列。"))
    elif ma5 < ma13 < ma20:
        risks.append("5/13/20 日线偏空排列，趋势结构较弱。")
        checks.append(RuleCheck("5/13/20结构", "风险", "均线偏空排列。"))
    else:
        observations.append("5/13/20 日线结构未完全统一，按震荡或观察处理。")
        checks.append(RuleCheck("5/13/20结构", "观察", "均线结构未完全统一。"))

    if volume > vol_ma5 * 1.3:
        observations.append("成交量较 5 日均量明显放大，需要结合位置判断是突破还是出货。")
        checks.append(RuleCheck("成交量", "观察", "成交量较 5 日均量明显放大。"))
    elif volume < vol_ma5 * 0.75:
        observations.append("成交量较 5 日均量缩小，属于缩量状态。")
        checks.append(RuleCheck("成交量", "观察", "成交量较 5 日均量缩小。"))
    else:
        checks.append(RuleCheck("成交量", "通过", "成交量未出现明显异常放大或萎缩。"))

    if volume > vol_ma20 * 1.5 and close < float(prev["close"]):
        risks.append("放量下跌，说明卖压较重。")
        checks.append(RuleCheck("放量下跌", "风险", "成交量明显放大且收盘下跌。"))
    else:
        checks.append(RuleCheck("放量下跌", "通过", "未触发放量下跌风险。"))

    twenty_day_high = float(recent_20["high"].max())
    twenty_day_low = float(recent_20["low"].min())
    position = (close - twenty_day_low) / (twenty_day_high - twenty_day_low) if twenty_day_high > twenty_day_low else 0.5

    if position > 0.85 and pct_chg > 3:
        risks.append("价格接近 20 日高位且涨幅较大，存在追高风险。")
        checks.append(RuleCheck("位置", "风险", "接近 20 日高位且涨幅较大。"))
    elif position < 0.35 and close > ma20:
        positives.append("位置相对不高且仍在 20 日线之上，可继续观察。")
        checks.append(RuleCheck("位置", "通过", "位置相对不高且在 20 日线之上。"))
    else:
        checks.append(RuleCheck("位置", "观察", "位置处于近 20 日区间中部或需结合量能判断。"))

    high_range = (twenty_day_high - twenty_day_low) / twenty_day_low if twenty_day_low else 0
    if high_range < 0.12:
        observations.append("近 20 日波动区间较窄，可能处于横盘阶段，横盘不买，等方向选择。")
        checks.append(RuleCheck("横盘", "观察", "近 20 日波动区间较窄，等方向选择。"))
    else:
        checks.append(RuleCheck("横盘", "通过", "近 20 日波动区间不属于窄幅横盘。"))

    recent_low = float(recent_20.iloc[:-1]["low"].min())
    if close < recent_low:
        risks.append("收盘价跌破近 20 日前低，触发破位风险。")
        checks.append(RuleCheck("破位", "风险", "收盘价跌破近 20 日前低。"))
    else:
        checks.append(RuleCheck("破位", "通过", "未跌破近 20 日前低。"))

    if turnover is not None:
        if turnover < 1:
            observations.append("换手率低于 1%，活跃度偏低。")
            checks.append(RuleCheck("换手率", "观察", "换手率低于 1%，活跃度偏低。"))
        elif 3 <= turnover <= 15:
            positives.append("换手率在 3%-15% 区间，短线活跃度较高。")
            checks.append(RuleCheck("换手率", "通过", "换手率在 3%-15% 区间。"))
        elif turnover > 20:
            risks.append("换手率超过 20%，波动较快，高位票风险更大。")
            checks.append(RuleCheck("换手率", "风险", "换手率超过 20%。"))
        else:
            checks.append(RuleCheck("换手率", "观察", "换手率处于中间区间，结合趋势判断。"))
    else:
        checks.append(RuleCheck("换手率", "数据不足", "未获取到换手率。"))

    if close > ma20 and close > ma5 and ma5 >= ma13:
        positives.append("符合 520 基础观察条件：站上 20 日线，并在 5/13 日线附近保持强势。")
        checks.append(RuleCheck("520基础条件", "通过", "站上 20 日线，且 5/13 日线附近保持强势。"))
    else:
        checks.append(RuleCheck("520基础条件", "观察", "尚未完全满足 520 基础观察条件。"))

    if high > close * 1.03 and volume > vol_ma5 * 1.2:
        risks.append("盘中冲高回落且放量，需要警惕冲高不封或兑现风险。")
        checks.append(RuleCheck("冲高回落", "风险", "盘中高点明显高于收盘且放量。"))
    else:
        checks.append(RuleCheck("冲高回落", "通过", "未触发明显冲高回落风险。"))

    conclusion = _make_conclusion(positives, risks, observations)
    risk_level = _make_risk_level(risks, observations)
    action_plan = _make_action_plan(conclusion, risks, positives, observations)
    return RuleResult(
        conclusion=conclusion,
        risk_level=risk_level,
        positives=positives,
        risks=risks,
        observations=observations,
        checks=checks,
        action_plan=action_plan,
    )


def _safe_float(value: object) -> float | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _make_conclusion(positives: list[str], risks: list[str], observations: list[str]) -> str:
    risk_text = " ".join(risks)
    if "破位" in risk_text:
        return "破位，按规则撤退或暂停参与。"
    if any("20 日线之下" in item for item in risks):
        return "不符合模式。"
    if any("追高风险" in item for item in risks):
        return "高位，不追。"
    if risks:
        return "触发风险，优先处理。"
    if len(positives) >= 4:
        return "观察，等待回踩确认。"
    if positives:
        return "观察。"
    return "不符合模式。"


def _make_risk_level(risks: list[str], observations: list[str]) -> str:
    risk_text = " ".join(risks)
    if "破位" in risk_text or "20 日线之下" in risk_text:
        return "高"
    if risks:
        return "中"
    if observations:
        return "观察"
    return "低"


def _make_action_plan(
    conclusion: str,
    risks: list[str],
    positives: list[str],
    observations: list[str],
) -> list[str]:
    plan: list[str] = []
    risk_text = " ".join(risks)
    if "破位" in risk_text:
        plan.append("已触发破位风险，按规则优先处理，不急着补仓。")
    if "20 日线之下" in risk_text:
        plan.append("未站上 20 日线，按规则不做多，等待重新站回后再观察。")
    if "追高风险" in risk_text:
        plan.append("位置偏高，不追，等待回踩确认。")
    if risks and not plan:
        plan.append("先处理风险，避免重仓和情绪化操作。")
    if positives and not risks:
        plan.append("已有正向条件，但仍按规则等待回踩或进一步确认。")
    if observations:
        plan.append("观察项需要结合后续量能、均线和位置变化继续确认。")
    if not plan:
        plan.append("不符合明确模式时，少看少动。")
    return plan
