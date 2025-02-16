from datetime import datetime
import calendar

def get_current_month_date_range():
    """Retorna a primeira e última data do mês atual."""
    now = datetime.now()
    start_date = datetime(now.year, now.month, 1)
    end_date = datetime(now.year, now.month, calendar.monthrange(now.year, now.month)[1], 23, 59, 59)
    return start_date, end_date
