import calendar
from datetime import datetime


def get_start_and_end_day_of_month(year=None, month=None):
    """Retorna a primeira e última data do mês especificado ou do mês atual se não informado."""
    now = datetime.now()
    year = year or now.year
    month = month or now.month

    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59)

    return start_date, end_date
