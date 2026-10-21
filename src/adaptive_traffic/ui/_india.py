"""India-specific rates for the impact model (dated, sourced, one place).

The impact numbers the dashboard shows are modelled (ILLUSTRATION). The prices
and rates used to price them are real and dated, so a reviewer can check them.

Sources for every constant below are in the comment next to it. Refresh this
file when the rates move; nothing else needs to change.
"""

AS_OF = "21 Oct 2026"
USD_INR = 94.77  # spot, 21 Oct 2026
LITRE_PER_US_GALLON = 3.78541

# city -> (petrol, diesel) in rupees per litre, retail pump price, 21 Oct 2026
# (IndianOil / PPAC trackers; outlets differ by a few paise)
FUEL_RATES = {
    "mumbai": (111.21, 97.83),
    "delhi": (102.12, 95.20),
    "bangalore": (111.68, 99.56),
    "surat": (101.82, 97.95),
}

VALUE_OF_TIME_INR_PER_HOUR = 100.0  # stated assumption: no current MoRTH figure to cite
IISD_SCC_USD_PER_TONNE = 86.0  # IISD social cost of carbon for India (2018), range 49-157
CARBON_INR_PER_TONNE = IISD_SCC_USD_PER_TONNE * USD_INR  # ~Rs 8,150/t
CO2_T_PER_CAR_YEAR = 1.55  # 12,000 km/yr at 17.9 km/l x 2.31 kg CO2 per litre
INDIA_FUEL_L_PER_100KM = 5.6  # IEA, Fuel Economy in Major Car Markets

# shortcut: the per-intersection volumes are constants scaled by the traffic
# input, not derived from it; upgrade to a traffic-derived model in the
# "impact model v2" work item (docs/MASTER_PLAN.md section 7).
VOLUME_SOURCE = "per-intersection constants scaled by your traffic figure"


def fuel_rates(city: str) -> tuple[float, float]:
    """(petrol, diesel) rupees per litre for a city; national average if unknown."""
    if city in FUEL_RATES:
        return FUEL_RATES[city]
    tracked = list(FUEL_RATES.values())
    petrol = sum(p for p, _ in tracked) / len(tracked)
    diesel = sum(d for _, d in tracked) / len(tracked)
    return round(petrol, 2), round(diesel, 2)


def _indian_group(n: int) -> str:
    """12345678 -> 1,23,45,678 (Indian digit grouping)."""
    s = str(n)
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    if head:
        parts.insert(0, head)
    return ",".join(parts + [tail])


def format_inr(value: float) -> str:
    """Full rupee amount with Indian grouping, e.g. Rs 5,24,00,000."""
    return f"₹{_indian_group(int(round(value)))}"


def format_inr_compact(value: float) -> str:
    """Short rupee amount: crore / lakh / plain, e.g. Rs 52.4 lakh."""
    if value >= 1e7:
        return f"₹{value / 1e7:.2f} crore"
    if value >= 1e5:
        return f"₹{value / 1e5:.1f} lakh"
    return f"₹{value:,.0f}"


def format_lakh_crore_hours(hours: float) -> str:
    """Hours in Indian units: 23 lakh hrs, 3.45 crore hrs."""
    if hours >= 1e7:
        return f"{hours / 1e7:.2f} crore hrs"
    if hours >= 1e5:
        return f"{hours / 1e5:.1f} lakh hrs"
    return f"{hours:,.0f} hrs"


def rates_line(city: str, with_usd: bool = True) -> str:
    """One-line price/rate strip for the reviewer."""
    petrol, diesel = fuel_rates(city)
    label = city.title() if city in FUEL_RATES else "national average"
    usd = f" · 1 USD = ₹{USD_INR}" if with_usd else ""
    return (
        f"Prices {AS_OF} · petrol ₹{petrol}/L ({label}) · diesel ₹{diesel}/L{usd} · "
        f"carbon ₹{CARBON_INR_PER_TONNE:,.0f}/t (IISD)"
    )
