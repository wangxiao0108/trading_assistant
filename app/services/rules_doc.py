from __future__ import annotations

from dataclasses import dataclass, field
from html import escape
from pathlib import Path
import re


PROJECT_DIR = Path(__file__).resolve().parents[2]
LEGACY_ROOT_DIR = Path(__file__).resolve().parents[3]
RULES_PATH = PROJECT_DIR / "我的交易系统V1.md"
LEGACY_RULES_PATH = LEGACY_ROOT_DIR / "我的交易系统V1.md"


@dataclass
class RulesSubsection:
    title: str
    html: str


@dataclass
class RulesSection:
    title: str
    intro_html: str = ""
    subsections: list[RulesSubsection] = field(default_factory=list)


@dataclass
class RulesDocument:
    title: str
    lead_html: str
    sections: list[RulesSection]


def load_rules_document() -> RulesDocument:
    rules_path = _resolve_rules_path()
    text = rules_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    title = "交易系统准则"
    lead_lines: list[str] = []
    sections: list[RulesSection] = []
    current_section: RulesSection | None = None
    current_subtitle: str | None = None
    current_body: list[str] = []

    def flush_subsection() -> None:
        nonlocal current_subtitle, current_body
        if current_subtitle is None:
            if current_section is not None and current_body:
                current_section.intro_html = _render_blocks(current_body)
        else:
            if current_section is not None:
                current_section.subsections.append(
                    RulesSubsection(title=current_subtitle, html=_render_blocks(current_body))
                )
        current_subtitle = None
        current_body = []

    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            continue

        if line.startswith("## "):
            flush_subsection()
            current_section = RulesSection(title=line[3:].strip())
            sections.append(current_section)
            continue

        if line.startswith("### "):
            flush_subsection()
            current_subtitle = line[4:].strip()
            continue

        if current_section is None:
            lead_lines.append(line)
        else:
            current_body.append(line)

    flush_subsection()
    return RulesDocument(title=title, lead_html=_render_blocks(lead_lines), sections=sections)


def _resolve_rules_path() -> Path:
    if RULES_PATH.exists():
        return RULES_PATH
    if LEGACY_RULES_PATH.exists():
        return LEGACY_RULES_PATH
    raise FileNotFoundError(
        f"未找到交易系统准则文档，请将 我的交易系统V1.md 放到项目目录：{PROJECT_DIR}"
    )


def load_520_document() -> RulesDocument:
    sections = [
        _make_520_section(
            "一、战法定位",
            [
                (
                    "模式边界",
                    [
                        "520战法是一套选股和交易模式，重点是固定模式、反复复盘和执行。",
                        "520战法多用于长期下跌后企稳、横盘整理一段时间，再出现反弹或反转的形态。",
                        "不符合520战法的交易不要做，不打板，不乱抄底，不在下降通道里猜底。",
                    ],
                ),
                (
                    "核心要求",
                    [
                        "进场点很重要，选股更重要。",
                        "要等走势企稳，等主力资金进场的信号出现，再考虑进场。",
                        "交易要做上升趋势里的确定性机会：趋势往上走，回调不破，再考虑上车。",
                    ],
                ),
            ],
        ),
        _make_520_section(
            "二、三条核心均线",
            [
                (
                    "均线含义",
                    [
                        "520选股法主要参考三条线：5日线、13日线、20日线。",
                        "5日线是短线操作的重要参考线之一。",
                        "13日线用于观察回踩、承接和波段节奏。",
                        "20日线是短线方向的生命线，也是重要风控位置。",
                    ],
                ),
                (
                    "纪律口令",
                    [
                        "20日线之上，不看空。",
                        "20日线之下，不做多。",
                        "股价连20日线都站不上去，就不适合参与。",
                        "只有站上20日线，又站上5日线，才属于短线强势个股，才有参与必要。",
                    ],
                ),
                (
                    "结构判断",
                    [
                        "20线在下方，13线在中间，5日线在上方，顺序发生改变，说明走势可能开始转强。",
                        "20线在上方，5日线压在下方，属于下降趋势，不适合操作。",
                        "多头排列、趋势向上，换手率在3%到10%之间，并且沿着5日线往上走，不必过度焦虑。",
                    ],
                ),
            ],
        ),
        _make_520_section(
            "三、选股形态",
            [
                (
                    "更好的形态",
                    [
                        "前面经历一轮下跌和横盘整理。",
                        "逐渐站上20日线和关键均线。",
                        "出现放量阳线、缩量阴线。",
                        "低点不断抬高，回踩有支撑。",
                        "上方不能有太多套牢盘，形态上要走出容易上攻的结构。",
                    ],
                ),
                (
                    "不急着买",
                    [
                        "买不到最低点很正常，能买在相对合理的位置即可。",
                        "不要看到别人拉大阳线就追，要等回踩。",
                        "严重破位的时候不要动手，急跌后的反弹不代表可以重仓炒作。",
                    ],
                ),
            ],
        ),
        _make_520_section(
            "四、买点条件",
            [
                (
                    "缩量回踩不破",
                    [
                        "较好的买点来自缩量回踩不破。",
                        "前面有放量上涨或突破动作。",
                        "回踩时量能缩小。",
                        "回踩不破趋势线或关键均线。",
                        "30分钟、60分钟图上仍有承接迹象。",
                        "再次上行时方向更明确。",
                    ],
                ),
                (
                    "放量突破确认",
                    [
                        "横盘之后，如果放量突破前方压力位，方向开始明确，再考虑进场。",
                        "如果只是放量但没有突破前高，不能简单认为是买点。",
                        "反弹过前高，才有机会走出反转的上升趋势。",
                    ],
                ),
                (
                    "买点位置",
                    [
                        "较好的买点不是最低点，而是放量阳线之后，股价没有跌破关键均线，仍然沿均线向上运行时。",
                        "可以等待回踩到阳线中部、底部或支撑附近再考虑。",
                    ],
                ),
            ],
        ),
        _make_520_section(
            "五、持仓处理",
            [
                (
                    "趋势未坏",
                    [
                        "趋势线不破、关键均线仍有支撑，不能简单判断为走坏。",
                        "如果持仓是放量突破后缩量回踩不破，后面就继续看趋势线、关键均线和量能。",
                        "修整不代表结束，回踩不破趋势就继续观察。",
                    ],
                ),
                (
                    "不乱做T",
                    [
                        "如果个股是多头排列、趋势向上，不要乱做T。",
                        "趋势好时，缩量阴线回调反而可能是加仓点。",
                        "带量上攻时，尽量不要轻易做T。",
                    ],
                ),
            ],
        ),
        _make_520_section(
            "六、卖点与风险",
            [
                (
                    "走弱信号",
                    [
                        "跌破20日线，就不该继续拿。",
                        "跌破13日线或关键趋势线，说明走势转弱。",
                        "冲高后不过前高，要小心回落。",
                        "该涨不涨时，要考虑先走。",
                    ],
                ),
                (
                    "高位风险",
                    [
                        "偏离5日线太远又不能封板时，要注意卖点。",
                        "放量冲高后无法延续，容易是假突破。",
                        "位置已经很高，又出现明显放量滞涨，要警惕短线兑现。",
                        "不在高位替别人接盘。",
                    ],
                ),
            ],
        ),
        _make_520_section(
            "七、仓位与纪律",
            [
                (
                    "仓位原则",
                    [
                        "技术不够时，仓位不要太重，减少乱动。",
                        "心态由仓位决定；仓位合理，才能按计划执行。",
                        "大盘弱、板块弱，好好休息；大盘弱、板块强，要控制仓位。",
                    ],
                ),
                (
                    "执行纪律",
                    [
                        "只做符合模式的机会。",
                        "不追高，耐心等回调。",
                        "少听消息面的杂音，按520模式来。",
                        "知道不代表会，稳定交易者真正难的是按规则做。",
                    ],
                ),
            ],
        ),
    ]
    lead_html = _render_blocks(
        [
            "> 本页内容由已整理的 520 战法规则提炼而成，并对重复表达做合并整理。",
        ]
    )
    return RulesDocument(title="520战法详解", lead_html=lead_html, sections=sections)


def _make_520_section(title: str, groups: list[tuple[str, list[str]]]) -> RulesSection:
    return RulesSection(
        title=title,
        subsections=[
            RulesSubsection(
                title=subtitle,
                html=_render_blocks([f"- {line}" for line in lines]),
            )
            for subtitle, lines in groups
        ],
    )


def _render_blocks(lines: list[str]) -> str:
    parts: list[str] = []
    paragraph: list[str] = []
    list_items: list[str] = []
    ordered_items: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            parts.append(f"<p>{escape(' '.join(item.strip() for item in paragraph))}</p>")
            paragraph = []

    def flush_list() -> None:
        nonlocal list_items
        if list_items:
            items = "".join(f"<li>{escape(item)}</li>" for item in list_items)
            parts.append(f"<ul>{items}</ul>")
            list_items = []

    def flush_ordered() -> None:
        nonlocal ordered_items
        if ordered_items:
            items = "".join(f"<li>{escape(item)}</li>" for item in ordered_items)
            parts.append(f"<ol>{items}</ol>")
            ordered_items = []

    def flush_all() -> None:
        flush_paragraph()
        flush_list()
        flush_ordered()

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            flush_all()
            continue

        if line.startswith(">"):
            flush_all()
            parts.append(f"<blockquote>{escape(line.lstrip('>').strip())}</blockquote>")
            continue

        if line.startswith("- "):
            flush_paragraph()
            flush_ordered()
            list_items.append(line[2:].strip())
            continue

        ordered_match = re.match(r"^\d+\.\s+(.*)$", line)
        if ordered_match:
            flush_paragraph()
            flush_list()
            ordered_items.append(ordered_match.group(1).strip())
            continue

        flush_list()
        flush_ordered()
        paragraph.append(line)

    flush_all()
    return "\n".join(parts)
