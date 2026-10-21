"""India rates, Indian number formatting, and no US units left in the UI."""

import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from adaptive_traffic.ui._india import (  # noqa: E402
    AS_OF,
    CARBON_INR_PER_TONNE,
    CO2_T_PER_CAR_YEAR,
    FUEL_RATES,
    IISD_SCC_USD_PER_TONNE,
    LITRE_PER_US_GALLON,
    USD_INR,
    VALUE_OF_TIME_INR_PER_HOUR,
    format_inr,
    format_inr_compact,
    format_lakh_crore_hours,
    fuel_rates,
    rates_line,
)

UI_DIR = SRC / "adaptive_traffic" / "ui"
RENDERED = list((UI_DIR / "views").glob("*.py")) + [UI_DIR / "app.py", UI_DIR / "theme.py"]


def test_indian_grouping():
    assert format_inr(12345678) == "₹1,23,45,678"
    assert format_inr(999) == "₹999"
    assert format_inr(100000) == "₹1,00,000"


def test_compact_rupee_units():
    assert format_inr_compact(5240000) == "₹52.4 lakh"
    assert format_inr_compact(230000000) == "₹23.00 crore"
    assert format_inr_compact(950) == "₹950"


def test_hour_units():
    assert format_lakh_crore_hours(2300000) == "23.0 lakh hrs"
    assert format_lakh_crore_hours(345000000) == "34.50 crore hrs"


def test_carbon_value_derives_from_iisd_usd_figure():
    assert CARBON_INR_PER_TONNE == IISD_SCC_USD_PER_TONNE * USD_INR
    assert 8000 < CARBON_INR_PER_TONNE < 8300  # ~Rs 8,150/t


def test_fuel_rates_cover_every_city_profile():
    profiles = {
        p.stem for p in (SRC / "adaptive_traffic" / "config" / "city_profiles").glob("*.json")
    }
    for city in profiles:
        petrol, diesel = fuel_rates(city)
        assert 80 < petrol < 130, city
        assert 80 < diesel < 130, city
    for city in FUEL_RATES:
        assert fuel_rates(city) == FUEL_RATES[city]


def test_unknown_city_falls_back_to_national_average():
    petrol, diesel = fuel_rates("tier2_default")
    tracked_p = [p for p, _ in FUEL_RATES.values()]
    assert petrol == round(sum(tracked_p) / len(tracked_p), 2)
    assert 0 < diesel < 130


def test_rates_line_carries_the_as_of_date():
    line = rates_line("mumbai")
    assert AS_OF in line
    assert "₹111.21" in line
    assert f"{USD_INR}" in line


def test_gallon_conversion_constant():
    assert LITRE_PER_US_GALLON == 3.78541
    assert abs(12450 * LITRE_PER_US_GALLON - 47128) < 5


def test_views_have_no_dollars_or_gallons():
    """Rendered UI must not show US currency or gallons any more."""
    for path in RENDERED:
        text = path.read_text(encoding="utf-8")
        assert "$" not in text, f"{path.name} still shows a dollar amount"
        assert not re.search(r"\bgal\b", text), f"{path.name} still uses gallons"


def test_time_value_is_declared_as_an_assumption():
    assert VALUE_OF_TIME_INR_PER_HOUR > 0
    assert CO2_T_PER_CAR_YEAR > 0
