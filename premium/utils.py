from datetime import datetime

from dateutil.relativedelta import relativedelta


def get_date_days_after(date: datetime, days: int) -> datetime:
    """Get the date one month after the given date."""
    return date + relativedelta(days=days)
