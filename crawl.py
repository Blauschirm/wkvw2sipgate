import requests, json, re, logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from sipgate_api import SipgateManager
from typing import List, Set, Dict, Tuple, Optional

logger = logging.getLogger('crawl')
logging.basicConfig(level=logging.DEBUG)

def build_url_for_month(base_url: str, year: int, month: int):
    relative_date_url = f"{year}-{str(month).rjust(2, '0')}/"
    url = base_url + relative_date_url
    return url

def get_html_of_month(base_url: str, year: int, month: int, login_payload=None, testing=False):
    url = build_url_for_month(base_url=base_url, year=year, month=month)

    logger.debug(f"Connecting to shift-server at {url}")

    r = requests.post(url, login_payload) if not testing else requests.get(url)
    if not r.ok:
        raise Exception(f"Request to '{url}' failed (HTTP Status Code {r.status_code}): Text: {r.text}")
    
    return r.content

def get_month_view(html_text: str):
    """
    Get's the month-view div from the html of a crawlable website.
    """
    CSS_CLASS_MONTH_VIEW = "month-view"
    
    soup = BeautifulSoup(html_text, 'html.parser')
    month_view = soup.find_all("div", attrs={"class": CSS_CLASS_MONTH_VIEW})
    if not month_view:
        raise Exception(f"Failed to find '.{CSS_CLASS_MONTH_VIEW}' in html", html_text)
    if len(month_view) != 1:
        raise Exception(f"Expected 1 month-view, found {len(month_view)}")
    return month_view[0]


def get_day_rows(month_view):
    """
    Parameters
    ----------
    month_view: soup of month view div

    Returns
    -------
    All tr-rows containing information for a day of the month each.
    """
    CSS_CLASS_DAY = "tag"
    
    all_days = month_view.find_all("td", attrs={"class": CSS_CLASS_DAY})
    if not all_days:
        raise Exception("Failed to find any days", month_view)

    day_rows = list(map(lambda day: day.parent, all_days))

    return day_rows[1:] # skip header row

def get_shifts_from_group(group):
    """
    Parameters
    ----------
    group: soup of a group (usually 2 shifts)

    Returns
    -------
    [shift8-20, shift20-8]
    """
    shifts = group.find_all("td")
    if not shifts:
        raise Exception("No shifts found in group", group)
        
    if len(shifts) != 2:
        raise Exception(f"Found {len(shifts)} in group but expected 2", group)

    return shifts

# @dataclass
class ShiftInfo:
    def __init__(self, name: str, phone_number: str, note: str = None):
        self.name = name
        self.phone_number = phone_number
        self.note = note
    
    def __repr__(self):
        return f"""ShiftInfo("{self.name}", "{self.phone_number}", "{self.note}")"""

def get_shift_info(shift) -> Optional[ShiftInfo]:
    """
    Parameters
    ----------
    shift: soup of a shift (e.g. for 20-8)
    """
    spans = shift.find_all("span")
    if not spans:
        return None
        # raise Exception("Found nothing in shift", shift)

    if len(spans) == 0:
        return None
    if len(spans) == 2:
        note_img = shift.find('img', {"class": "telinfo"}) # there's a note attached to this
        note = note_img.get("title") if note_img else None

        return ShiftInfo(name=spans[0].text,
            phone_number=spans[1].text,
            note=note)

    raise Exception(f"Found {len(spans)} spans in shift, expected 0 or 2", shift, spans)

class DayInfo:
    def __init__(self, day: str, groups: List[List[Optional[ShiftInfo]]], note: ShiftInfo = None):
        self.day = day
        self.groups = groups
        self.note = note
    
    def __repr__(self):
        return f"""DayInfo("{self.day}", "{self.groups}", "{self.note}")"""


def get_day_info(day_row) -> DayInfo:
    """
    Parameters
    ----------
    day_row: soup of a day's row (tr)

    Returns
    -------
    The shift groups of a day

    Remarks
    ------
    Instead of getting by class we could return all <td>s
        Except the first one (which is the date)
        Except the last one (which is a Note/Anmerkung) <- nitzel@blauschirm Do we need the last column?
    """
    CSS_CLASS_GROUP_DIVIDER = "trenner"

    tds = day_row.find_all("td")
    groups = day_row.find_all("td", {"class": CSS_CLASS_GROUP_DIVIDER})
    groups = map(lambda group: list(map(get_shift_info, get_shifts_from_group(group))), groups)
    return DayInfo(day=tds[0].text.strip(),
        groups=list(groups),
        note=get_shift_info(tds[-1]))

if __name__ == "__main__":
    html = get_html_of_month("http://localhost:8081/", 2019, 7, testing=True)

    month_view = get_month_view(html)
    day_rows = get_day_rows(month_view)

    for i, day_row in enumerate(day_rows):
        try:
            day_info = get_day_info(day_row)
            print(f"{i}. row: {day_info.day}, note: {day_info.note}")
            for group_id, shifts in enumerate(day_info.groups):
                print(f"  Group {group_id}")
                for shift_id, shift in enumerate(shifts):
                    print(f"    Shift {shift_id} {shift}")
        except Exception as exception:
            print(i, "EXC", exception)

    
