import os

from yield_data import WAREHOUSE_DB  # noqa: F401  (kept for import symmetry)
from yield_data import YIELD_MIN, YIELD_MAX


class QualityError(Exception):
    def __init__(self, msg):
        self.msg = f"YIELD_DATA: {msg}"
        super().__init__(self.msg)


def _band() -> tuple[float, float]:
    low = float(os.environ.get("YIELD_MIN", YIELD_MIN))
    high = float(os.environ.get("YIELD_MAX", YIELD_MAX))
    return low, high


def not_null_quality_check(rows) -> None:
    """Every row must have a non-null Tenor, Trading Date, and Yield."""
    for tenor, trading_date, value in rows:
        if not tenor or not trading_date or value is None:
            raise QualityError(
                f"Not null quality check failed for row ({tenor!r}, {trading_date!r}, {value!r})"
            )


def within_band_quality_check(rows) -> None:
    """Yield-appropriate range check (a rate, not a Daily Bar).

    Deliberately does NOT apply the equity ``volume > 0`` / ``HIGH >= LOW`` rules.
    """
    low, high = _band()
    for tenor, trading_date, value in rows:
        if value < low or value > high:
            raise QualityError(
                f"Yield {value} for ({tenor}, {trading_date}) is outside the sane band [{low}, {high}]"
            )


def perform_quality_checks(rows):
    """Validate the whole batch before any write; raise on the first violation."""
    not_null_quality_check(rows)
    within_band_quality_check(rows)
    return rows
