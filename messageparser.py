import re
from typing import List, Set, Dict, Tuple, Optional
import logging
from enum import Enum

regex_valid_time = r"\d{1,2}\:\d\d"
regex_from_to = re.compile(f" (?P<from>{regex_valid_time}) (?:uhr)? - (?P<to>{regex_valid_time}) (?:uhr)?".replace(' ', r'\s*'))
regex_from_or_to = re.compile(f" (?P<fromOrTo>(?:bis)|(?:ab)) (?P<time>{regex_valid_time})".replace(' ', r'\s*'))


class FromOrTill(Enum):
    FROM = 'ab'
    TILL = 'bis'


class TimeRule(object):
    def __init__(self, time: str, from_or_till: FromOrTill, phone_number: str, pair_id: int = None):
        self.time = time
        self.from_or_till = from_or_till
        self.pair_id = pair_id
        self.phone_number = phone_number
        # a comes before z, as FROM should be before TILL
        self.sortable_key = f"{self.time}{'a' if self.from_or_till == FromOrTill.FROM else 'z'}"

    def __repr__(self):
        return f"""TimeRule(time="{self.time}", from_or_till="{self.from_or_till}", pair_id={self.pair_id}, phone_number="{self.phone_number}")"""

    def __str__(self):
        return f"[TimeRule<{self.from_or_till} {self.time}, pair={self.pair_id}, number={self.phone_number}>]"

    def __eq__(self, other) -> bool:
        """
        Equality based only on `pair_id` and `phone_number`!
        """
        return (self.pair_id == other.pair_id) and (self.phone_number == other.phone_number)

    @staticmethod
    def sort(rules: List) -> List:
        return sorted(rules, key=lambda rule: rule.sortable_key)


def parse_rules_from_message(shift_start: str, shift_end: str, default_number: str, message: str):
    logger = logging.getLogger("Parser")
    logger.debug(f"Processing text '{message}'")

    # pad all hours, 9:12 -> 09:12 
    message = message.lower()
    re.sub(r"(?<=\D)(\d:\d\d)", r"0\1", message)
    rules: List[TimeRule] = []
    pair_id = 1

    for substitute in message.split(';'):
        logger.debug(f"Processing substitute '{substitute}'")

        numbers = re.findall(r"(?:\s)\+?\d{5,}", substitute)
        if len(numbers) != 1:
            logger.error(f"Found {len(numbers)} telephone numbers in substitute segment '{substitute}' but expected only one")
            continue

        number = numbers[0].strip()
        logger.debug(f"  Found phone number '{number}' in substitute '{substitute}'")

        for timeslot in re.split(r"(?:und)|,", substitute):
            logger.debug(f"  Processing timeslot '{timeslot}'")

            matches = regex_from_to.match(timeslot)
            if matches:
                # matches 12:30- 13:20 and 12:30 Uhr - 13:20 Uhr
                time_from, time_till = matches.group('from'), matches.group('to')
                logger.debug(f"    Extracted timeslot '{time_from}' to '{time_till}'")
                rules.append(TimeRule(time=time_from, from_or_till=FromOrTill.FROM, phone_number=number, pair_id=pair_id))
                rules.append(TimeRule(time=time_till, from_or_till=FromOrTill.TILL, phone_number=number, pair_id=pair_id))
                pair_id += 1
                continue

            matches = regex_from_or_to.match(timeslot)
            if matches:
                # Matches 'ab 13:20' or 'bis 13:20'
                prefix, time = matches.group('fromOrTo'), matches.group('time')
                logger.debug(f"    Extracted timeslot '{prefix}' '{time}'")
                if prefix == 'bis':
                    logger.debug(f"    Equivalent to '{shift_start}' '{time}'")
                    rules.append(TimeRule(time=shift_start, from_or_till=FromOrTill.FROM, phone_number=number))
                    rules.append(TimeRule(time=time, from_or_till=FromOrTill.TILL, phone_number=number))
                    continue
                elif prefix == 'ab':
                    logger.debug(f"    Equivalent to '{time}' '{shift_end}'")
                    rules.append(TimeRule(time=time, from_or_till=FromOrTill.FROM, phone_number=number))
                    rules.append(TimeRule(time=shift_end, from_or_till=FromOrTill.TILL, phone_number=number))  # superfluous
                    continue
                raise Exception(f"Failed to parse timeslot '{timeslot}', this should never happen")

            logger.error(f"    Failed to parse timeslot '{timeslot}', make sure to use the format 'hh:mm - hh:mm' or 'ab hh:mm' or 'bis hh:mm'")

    if not any(rule.time == shift_start for rule in rules):
        rules.append(TimeRule(time=shift_start, from_or_till=FromOrTill.FROM, phone_number=default_number))

    return TimeRule.sort(rules)


def time_rules_to_interval_list(rules: List[TimeRule], default_number: str, shift_end: str):
    # tricky: we have to translate the rules into a continuous list of intervals with the correct number for that interval
    # If we encouter a substitution ending rule, we need to change back to the previous number, so we need a stack to keep
    # track of the currently active numbers and take the most recent one of those

    intervals = []
    # On the stack only the phone_number and pair_id are relevant
    stack: List[TimeRule] = [TimeRule("", FromOrTill.FROM, default_number, None)]
    for rule in rules:
        if rule.from_or_till == FromOrTill.FROM:
            stack.insert(0, rule) # the top of the stack is at 0, this is needes because the remove function scans an array from left to right.
        else: # TILL
            if rule in stack:
                stack.remove(rule)  # remove previously added FROM with same phone_number & pair_id

        intervals.append([rule.time, stack[0].phone_number])

    for i in range(len(intervals) - 1):
        intervals[i].insert(1, intervals[i + 1][0])
    intervals[-1].insert(1, shift_end)

    no_empty_intervals = filter(lambda interval: interval[0] != interval[1], intervals)
    return list(no_empty_intervals)


def get_interval_list_from_message(shift_start: str, shift_end: str, default_number: str, message: str):
    """
    Returns a list of time intervals with the given phone number for the interval, according to a string with correct formatting
    all times are handled as "24:00" strings

    # Format: Uhrzeiten immer mit Doppelpunkt und Minuten als hh:mm
    # Zeitintervalle mit Bindestrich kennzeichnen "12:00 - 13:00". Leerzeichen sind optional.
    # offene Angaben mit Schlüsselwoertern "bis" und "ab" vor der Uhrzeit. Gilt ab oder bis Schichtende bzw. -Anfang.
    # Telefonnummern ohne Sonder- oder Leerzeichen außer '+'.
    # Verschiedene Vetretungen mit Semikolon trennen ";"
    # Mehrere Uhrzeitbereiche für die selbe Vertretung können mit Komma und "und" aneinander gereiht werden.
    # Beispiel: "bis 10:00 Uhr +491234; bis 12:20, 13:00-14:20 und ab 17:00 Uhr +494321"
    #
    # timeslots |                     |          |              |                      | 
    # segment   |                     |                                                |

    Parameters:
    shift_start (string): regular beginning of shift
    shift_end (string): regular end of shift
    default_number (string): regular phone number for this shift
    message (string): content of the comment box, which gets parsed into the substitution rules 

    Returns:
    intervals      (list of lists): list of lists with format [interval_start, interval_end, phone_number]
    """

    rules = parse_rules_from_message(shift_start=shift_start,
                                     shift_end=shift_end,
                                     default_number=default_number,
                                     message=message)
    return time_rules_to_interval_list(rules, default_number, shift_end)
