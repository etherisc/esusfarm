from loguru import logger
from pydantic import BaseModel

from server.error import raise_with_log

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

class Date(BaseModel):

    date:datetime

    @classmethod
    def create_from(cls, input_date):
        if isinstance(input_date, str):
            return Date(date = datetime.fromisoformat(input_date))
        elif isinstance(input_date, datetime):
            return Date(date = datetime.combine(input_date.date(), datetime.min.time()))
        elif isinstance(input_date, Date):
            return Date(date = input_date.date)
        else:
            raise_with_log(TypeError, f"invalid date type {type(input_date)}, expected: iso date string or python date")

    def __str__(self):
        return self.to_iso_string()

    __repr__ = __str__

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Date):
            return NotImplemented
        return self.date == other.date

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, Date):
            return NotImplemented
        return self.date != other.date

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Date):
            return NotImplemented
        return self.date > other.date

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Date):
            return NotImplemented
        return self.date >= other.date

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Date):
            return NotImplemented
        return self.date < other.date

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Date):
            return NotImplemented
        return self.date <= other.date

    def to_iso_string(self):
        return date_to_format(self.date, ISO_DATE)

    def to_python_date(self):
        return self.date

    def add(self, days:int) -> 'Date':
        self.date += timedelta(days=days)
        return self

    def create_sequence(self, days:int) -> list['Date']:
        return [Date.create_from(self.date + timedelta(days=i)) for i in range(days)]

    @classmethod
    def min(cls) -> 'Date':
        return cls.create_from('1900-01-01')

    @classmethod
    def today(cls) -> 'Date':
        return cls.create_from(datetime.today())

    @classmethod
    def january_1st(cls, year:int=None):
        if not year:
            return cls.create_from(datetime(datetime.today().year, 1, 1))

        return cls.create_from(datetime(year, 1, 1))


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
        raise_with_log(ValueError, f"Invalid month name '{month_str}'")

    month = list(month_name).index(month_str)
    days_up_to_month = sum(monthrange(year, m)[1] for m in range(1, month))
    days_in_this_month = min(7 * (week - 1) + 1, monthrange(year, month)[1])

    return days_up_to_month + days_in_this_month


def day_in_year_to_iso(year: int, day_in_year: int) -> str:
    year_start = date(year, 1, 1)
    target_date = year_start + timedelta(days=day_in_year - 1)
    return target_date.isoformat()


def decad_to_iso(decad_date:str) -> str:
    if not decad_date or len(decad_date) == 0:
        return None

    token = map(int, decad_str.split('-D'))
    if not len(token) == 2:
        return None

    (year, decad) = map(int, token)
    if year < 1900 or year > 2100:
        return None
    
    # decad <= 0 is in the previous year(s), decad >= 38 is in the following year(s)
    if decad < 1 or decad > 37:
        return None

    start_date = datetime(year, 1, 1)
    target_date = start_date + timedelta(days=(decad - 1) * 10)
    return target_date.isoformat()


def iso_to_decad(iso_date:str) -> str:
    if not iso_date or len(iso_date) == 0:
        return None

    date = datetime.strptime(iso_date_str, '%Y-%m-%d')
    start_date = datetime(date_obj.year, 1, 1)
    delta = date - start_date
    decad = (delta.days // 10) + 1
    return f"{date.year}-D{decad}"



def print_stuff(year: int):
    for month in range(1, len(month_name)):
        for week in range(1, 6):
            doy = day_of_year(year, month_name[month], week)
            iso = day_in_year_to_iso(year, doy)

            print(f"{year} {month_name[month]} {week} {doy} {iso}")
