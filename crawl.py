import requests, json, re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from sipgate_api import SipgateManager
from typing import List, Set, Dict, Tuple, Optional
from dataclasses import dataclass
from messageparser import get_interval_list_from_message


@dataclass
class ShiftInfo:
    """
    Information about a single shift
        - Who's shift it is
        - His phone number
        - A note about it
    """
    name: str
    phone_number: str
    note: Optional[str]


@dataclass
class DayInfo:
    """
    Information about an entire day:
        - The description of the day (e.g. 1. Freitag)
        - The groups and their shifts
        - A note about it
    """
    day: str
    groups: List[List[Optional[ShiftInfo]]]
    note: Optional[ShiftInfo]


def build_url_for_month(base_url: str, year: int, month: int):
    relative_date_url = f"{year}-{str(month).rjust(2, '0')}/"
    url = base_url + relative_date_url
    return url


def get_html_of_month(base_url: str, year: int, month: int, login_payload=None, testing=False):
    url = build_url_for_month(base_url=base_url, year=year, month=month)

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


@dataclass
class TimeSlot(object):
    start_time: str
    end_time: str
    phone_number: str

    def __str__(self):
        return f"{self.start_time} - {self.phone_number} (ends {self.end_time})"

def parse_day_info(
    day_info: DayInfo,
    group_id: int,
    shift_starts: List[str],
    shift_ends: List[str],
    default_number: str) -> List[TimeSlot]:
    """
    Parses given day's group into a list of TimeSlots.

    Parameters
    ----------
    shift_starts: List of times where the corresponding nth shift starts
    shift_ends: List of times where the corresponding nth shift ends
    default_number: If there is no number given
    """
    shifts = day_info.groups[group_id]

    return [
        TimeSlot(*interval) for shift_id, shift in enumerate(shifts) for interval in get_interval_list_from_message(
            shift_starts[shift_id],
            shift_ends[shift_id],
            shift and shift.phone_number or DEFAULT_NUMBER,
            shift and shift.note or "")
    ]

def get_month():
    # Constants
    SHIFT_STARTS = ["08:00", "20:00"]
    SHIFT_ENDS = ["20:00", "08:00"]

    # Read config to even more constants
    with open('config.json', 'r') as config_file:
        config_data = json.load(config_file)
    TESTING = config_data["TESTING"]
    DEFAULT_NUMBER = config_data["fallback_phone_number"]
    BASE_URL = config_data["test_base_url" if TESTING else "real_base_url"]
    LOGIN_PAYLOAD = config_data["schedule_login_payload"]

    # Get HTML of website
    html = get_html_of_month(
        base_url=BASE_URL,
        year=2019, 
        month=5, 
        login_payload=LOGIN_PAYLOAD,
        testing=TESTING)

    # Get day rows from html
    month_view = get_month_view(html)
    day_rows = get_day_rows(month_view)


    day_infos = list(map(lambda day_row: get_day_info(day_row), day_rows))

    parsed_days = list(map(lambda day_info: [parse_day_info(day_info, group_id, SHIFT_STARTS, SHIFT_ENDS, DEFAULT_NUMBER) for group_id in range(len(day_info.groups))], day_infos))
    
    return parsed_day

if __name__ == "__main__":
    # Constants
    SHIFT_STARTS = ["08:00", "20:00"]
    SHIFT_ENDS = ["20:00", "08:00"]

    # Read config to even more constants
    with open('config.json', 'r') as config_file:
        config_data = json.load(config_file)
    TESTING = config_data["TESTING"]
    DEFAULT_NUMBER = config_data["fallback_phone_number"]
    BASE_URL = config_data["test_base_url" if TESTING else "real_base_url"]
    LOGIN_PAYLOAD = config_data["schedule_login_payload"]

    # Get HTML of website
    html = get_html_of_month(
        base_url=BASE_URL,
        year=2019, 
        month=5, 
        login_payload=LOGIN_PAYLOAD,
        testing=TESTING)

    # Get day rows from html
    month_view = get_month_view(html)
    day_rows = get_day_rows(month_view)


    day_infos = list(map(lambda day_row: get_day_info(day_row), day_rows))

    parsed_days = list(map(lambda day_info: [parse_day_info(day_info, group_id, SHIFT_STARTS, SHIFT_ENDS, DEFAULT_NUMBER) for group_id in range(len(day_info.groups))], day_infos))
    
    # exit()
    # for day_id, pday in enumerate(parsed_days):
    day_id = 4
    pday = parsed_days[day_id]
    for shift_id, shift_name in enumerate(["NFS1", "NFS2", "Leitung"]):
        print(day_id + 1, shift_name)
        for p in pday[shift_id]:
            print("  ", str(p))
    exit()
    # Parse the day rows into DayInfos and print them with their shifts
    for i, day_row in enumerate(day_rows):
        try:
            day_info = get_day_info(day_row)
            print(f"{i}. row: {day_info.day}, note: {day_info.note}")
            for group_id, shifts in enumerate(day_info.groups):
                print(f"  Group {group_id}")
                for start_time, phone_number in [
                    [interval[0], interval[2]] for shift_id, shift in enumerate(shifts) for interval in get_interval_list_from_message(
                        SHIFT_STARTS[shift_id],
                        SHIFT_ENDS[shift_id],
                        shift and shift.phone_number or DEFAULT_NUMBER,
                        shift and shift.note or "")]:
                    print("   ", start_time, phone_number)
        except Exception as exception:
            print(i, "EXC", exception)
            raise

    
