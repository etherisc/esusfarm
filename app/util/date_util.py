from loguru import logger

from calendar import (
    month_name,
    monthrange
)

from datetime import (
    date,
    datetime,
    timedelta
)

ISO_DATE = '%Y-%m-%d'
DATE_MIN = date(1900, 1, 1)
DATE_MAX = date(2100, 12, 31)


def add_days(a_date: date, days:int) -> date:
    return a_date + timedelta(days=days)


def get_today_iso() -> str:
    return date_to_iso(date.today()) 


def date_to_iso(a_date: date) -> str:
    return date_to_format(a_date, ISO_DATE)


def date_to_format(a_date: date, date_format: str) -> str:
    return a_date.strftime(date_format)


def date_from_iso(iso_date: str) -> date:
    return date.fromisoformat(iso_date)


def date_from_format(a_date: str, date_format: str) -> date:
    return datetime.strptime(a_date, date_format).date()


def get_iso_datetime(timestamp:str):
    return datetime.fromtimestamp(timestamp).isoformat()


def timestamp_to_iso_date(timestamp:int) -> str:
    if timestamp == 0:
        return None

    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d")


def iso_date_to_timestamp(iso_date:str) -> int:
    if not iso_date or len(iso_date) == 0:
        return None

    dt = datetime.strptime(iso_date, "%Y-%m-%d")
    return int(dt.timestamp())


def get_iso_date_range(from_date:date, to_date:date):
    # logger.info('inside, start {} end {} ts {} te {}'.format(start_date, end_date, type(start_date), type(end_date)))
    # from_date = date.fromisoformat(start_date)
    # to_date = date.fromisoformat(end_date)
    delta = to_date - from_date

    if delta.days < 0:
        return []

    return [(from_date + timedelta(days=i)).isoformat() for i in range(delta.days + 1)]


def day_of_year(year: int, month_str: str, week: int) -> int:
    if not month_str in list(month_name):
        raise_with_log(f"Invalid month name '{month_str}'")

    month = list(month_name).index(month_str)
    days_up_to_month = sum(monthrange(year, m)[1] for m in range(1, month))
    days_in_this_month = min(7 * (week - 1) + 1, monthrange(year, month)[1])

    return days_up_to_month + days_in_this_month


def day_in_year_to_iso(year: int, day_in_year: int) -> str:
    year_start = date(year, 1, 1)
    target_date = year_start + timedelta(days=day_in_year - 1)
    return target_date.isoformat()


def decad_to_iso(decad_date:str) -> str:
    if not isinstance(decad_date, str):
        raise_with_log(f"Decad '{decad_date}' not string. Expected format 'YYYY-Dnn'")

    if not decad_date or len(decad_date) == 0:
        return None

    token = decad_date.split('-D')
    if not len(token) == 2:
        raise_with_log(f"Invalid decad format '{decad_date}'. Expected format 'YYYY-Dnn'")

    (year, decad) = map(int, token)
    if year < 1900 or year > 2100:
        raise_with_log(f"Invalid year '{year}'. Valid range: 1900-2100")
    
    # decad <= 0 is in the previous year(s), decad >= 38 is in the following year(s)
    if decad < 1 or decad > 37:
        raise_with_log(f"Invalid decad '{decad}'. Valid range: 1-37")

    start_date = datetime(year, 1, 1)
    target_date = start_date + timedelta(days=(decad - 1) * 10)
    return date_to_iso(target_date)


def iso_to_decad(iso_date:str) -> str:
    if not isinstance(iso_date, str):
        raise_with_log(f"date '{iso_date}' not string. Expected format 'YYYY-MM-DD'")

    if not iso_date or len(iso_date) == 0:
        return None

    date = datetime.strptime(iso_date, '%Y-%m-%d')
    start_date = datetime(date.year, 1, 1)
    delta = date - start_date
    decad = (delta.days // 10) + 1
    return f"{date.year}-D{decad}"


def raise_with_log(error_message:str):
    logger.warning(error_message)
    raise ValueError(error_message)