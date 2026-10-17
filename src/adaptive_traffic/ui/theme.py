"""Single design system for all UI views (no per-page hex, no emoji icons).

Palette: slate text, white cards, one accent + three status colors.
Icons: hand-built inline SVG (stroke style), identical on every OS.
"""

INK = "#0f172a"
MUTED = "#64748b"
ACCENT = "#2563eb"
OK = "#16a34a"
WARN = "#d97706"
BAD = "#dc2626"
CARD_BG = "#ffffff"
PAGE_BG = "#f8fafc"

# shortcut: icons are geometric primitives (rect/circle/line), not brand paths;
# upgrade to Lucide files only if a designer hands us the set.
_ICONS = {
    "camera": '<rect x="3" y="7" width="18" height="13" rx="2"/><circle cx="12" cy="13" r="3.5"/><path d="M8 7l1.5-2.5h5L16 7"/>',  # noqa: E501
    "cpu": '<rect x="6" y="6" width="12" height="12" rx="2"/><rect x="10" y="10" width="4" height="4"/><path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/>',  # noqa: E501
    "signal": '<rect x="7" y="2" width="10" height="20" rx="5"/><circle cx="12" cy="7" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="12" cy="17" r="1.6"/>',  # noqa: E501
    "car": '<path d="M4 13l1.5-4.5A2 2 0 0 1 7.4 7h9.2a2 2 0 0 1 1.9 1.5L20 13"/><rect x="3" y="13" width="18" height="5" rx="1.5"/><circle cx="7.5" cy="18" r="1.6"/><circle cx="16.5" cy="18" r="1.6"/>',  # noqa: E501
    "pulse": '<path d="M2 12h4l3-7 4 14 3-7h6"/>',
    "gauge": '<path d="M4 14a8 8 0 1 1 16 0"/><path d="M12 14l4.5-4.5"/><path d="M4 18h16"/>',  # noqa: E501
    "leaf": '<path d="M5 19C5 9 13 5 20 4c0 8-4 15-13 15"/><path d="M5 19c3-5 7-9 11-11"/>',  # noqa: E501
    "check": '<circle cx="12" cy="12" r="9"/><path d="M8.5 12.5l2.5 2.5 4.5-5.5"/>',
}


def svg(name: str, size: int = 20, color: str = "currentColor") -> str:
    """Inline SVG icon string for st.markdown(unsafe_allow_html=True)."""
    body = _ICONS.get(name, _ICONS["check"])
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="1.8" stroke-linecap="round" '
        f'stroke-linejoin="round" style="vertical-align:-3px" '
        f'aria-hidden="true" focusable="false">{body}</svg>'
    )


def heading(icon: str, text: str, level: int = 2, icon_size: int = 24) -> str:
    """Full HTML heading with icon — render with st.html (markdown escapes it)."""
    return (
        f"<h{level} style='color:{INK};margin-bottom:.6rem'>"
        f"{svg(icon, icon_size, ACCENT)} {text}</h{level}>"
    )


def steps(items: list[tuple[str, str, str]]) -> str:
    """Numbered icon list as HTML. items = (icon, bold_lead, rest)."""
    rows = "".join(
        f"<li style='margin:.3rem 0'>{svg(ic, 17, ACCENT)} <b>{lead}</b> — {rest}</li>"
        for ic, lead, rest in items
    )
    return f"<ol style='padding-left:1.2rem;color:{INK}'>{rows}</ol>"


_CHIP = {
    "MEASURED": ("#166534", "#dcfce7"),
    "ILLUSTRATION": ("#92400e", "#fef3c7"),
    "SPEC": ("#334155", "#e2e8f0"),
}


def chip(text: str) -> str:
    """Pill marking a block as MEASURED / ILLUSTRATION / SPEC."""
    fg, bg = _CHIP.get(text.upper(), _CHIP["SPEC"])
    return (
        f"<span style='display:inline-block;background:{bg};color:{fg};border-radius:999px;"
        f"padding:.1rem .45rem;font-size:.75rem;font-weight:700;letter-spacing:.03em;"
        f"margin-right:.4rem;white-space:nowrap'>{text.upper()}</span>"
    )


def tagline(tag: str, text: str) -> str:
    """Group-level truth marker: chip + one plain-English line."""
    return (
        f"<div style='margin:.1rem 0 .5rem;color:{INK};font-size:.88rem'>"
        f"{chip(tag)} {text}</div>"
    )


def banner(text: str, tag: str = "ILLUSTRATION") -> str:
    """Page-level truth banner."""
    return (
        f"<div style='background:#fffbeb;border:1px solid #fcd34d;border-radius:8px;"
        f"padding:.6rem .8rem;margin-bottom:.8rem;color:{INK};font-size:.9rem'>"
        f"{chip(tag)} {text}</div>"
    )


def card(title: str, value: str, sub: str = "", tone: str = ACCENT, icon: str = "") -> str:
    """Status card HTML. tone = accent/ok/warn/bad hex; icon = key in _ICONS."""
    mark = f"{svg(icon, 18, tone)} " if icon else ""
    dot = (
        f"<span style='display:inline-block;width:8px;height:8px;border-radius:50%;"
        f"background:{tone};margin-right:.4rem'></span>"
    )
    subrow = f"<p style='margin:.15rem 0 0;color:{MUTED};font-size:.82rem'>{sub}</p>" if sub else ""
    return (
        f"<div style='background:{CARD_BG};border:1px solid #e2e8f0;"
        f"border-radius:10px;padding:.8rem 1rem;box-shadow:0 1px 3px rgba(15,23,42,.06)'>"
        f"<div style='color:{MUTED};font-size:.8rem;font-weight:600'>{dot}{mark}{title}</div>"
        f"<div style='font-size:1.55rem;font-weight:700;color:{INK};margin-top:.15rem'>"
        f"{value}</div>"
        f"{subrow}</div>"
    )


BASE_CSS = f"""
<style>
.stApp {{ background:{PAGE_BG}; color:{INK}; }}
.main-header {{ font-size:2.1rem; color:{INK}; text-align:center; margin-bottom:.4rem; }}
.subheader {{ font-size:1.25rem; color:{INK}; margin-bottom:.6rem; }}
.metric-card {{ background:{CARD_BG}; border:1px solid #e2e8f0; border-radius:10px;
    padding:1rem; box-shadow:0 1px 3px rgba(15,23,42,.06); text-align:center; }}
.model-badge {{ background:#eff6ff; border:1px solid #bfdbfe; color:#1d4ed8; border-radius:8px;
    padding:.45rem .6rem; font-size:.78rem; margin-top:.6rem; }}
button:focus-visible, a:focus-visible, input:focus-visible,
[role="tab"]:focus-visible, [role="radio"]:focus-visible,
[role="checkbox"]:focus-visible, [data-testid="stSlider"] input:focus-visible {{
    outline:2px solid {ACCENT} !important; outline-offset:2px; }}
/* the radio input itself is clipped by Streamlit, so ring the visible label */
[data-testid="stRadioOption"] label:has(input:focus-visible) {{
    outline:2px solid {ACCENT} !important; outline-offset:2px; border-radius:6px; }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{
    color:#475569; opacity:1 !important; }}
[data-testid="stAlertContentSuccess"] p {{ color:#14532d; }}
[data-testid="stBaseButton-elementToolbar"] {{ display:none; }}
[data-testid="stAppDeployButton"] {{ display:none; }}
.stMarkdown p {{ max-width:78ch; }}
[data-testid="stCode"] .token.punctuation {{ color:#475569 !important; }}
[data-testid="stCode"] .token.parameter,
[data-testid="stCode"] .token.variable {{ color:#1d4ed8 !important; }}
[data-testid="stCode"] .token.number {{ color:#0f766e !important; }}
[data-testid="stCode"] .token.keyword {{ color:#7c3aed !important; }}
[data-testid="stCode"] .token.string {{ color:#b45309 !important; }}
[data-testid="stCode"] .token.comment {{ color:#475569 !important; }}
.explanation-box {{ background:#eff6ff; border:1px solid #bfdbfe; border-radius:8px;
    padding:.6rem .8rem; margin-bottom:.8rem; }}
</style>
"""
