import re
from typing import List, Set, Dict, Tuple, Optional
import logging

regex_valid_time = r"\d{1,2}\:\d\d"
regex_from_to = re.compile(f" (?P<from>{regex_valid_time}) (?:uhr)? - (?P<to>{regex_valid_time}) (?:uhr)?".replace(' ', r'\s*'))
regex_from_or_to = re.compile(f" (?P<fromOrTo>(?:bis)|(?:ab)) (?P<time>{regex_valid_time})".replace(' ', r'\s*'))

def parse(shift_start: str, shift_end: str, default_number: str, text_content: str):
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
    # timeslots |           |          |          |              |             | 
    # segment   |                     |                                         |

    Parameters:
    shift_start (string): regular beginning of shift
    shift_end   (string): regular end of shift
    default_number (string): regular phone number for this shift
    text_content   (string): content of the comment box, which gets parsed into the substitution rules 

    Returns:
    intervals      (list of lists): list of lists with format [interval_start, interval_end, phone_number]
    """

    logger = logging.getLogger("Parser")
    logger.debug(f"Processing text '{text_content}'")

    # pad all hours, 9:12 -> 09:12 
    text_content = text_content.lower()
    re.sub(r"(?<=\D)(\d:\d\d)", r"0\1", text_content)
    rules = []
    pair_id = 1

    for substitute in text_content.split(';'):
        logger.debug(f"Processing substitute '{substitute}'")

        numbers = re.findall(r"(?:\s)\+?\d{5,}", substitute)
        if len(numbers) != 1:
            logger.error(f"Found {len(numbers)} telephone numbers in substitute segment '{substitute}' but expected only one")
            continue

        number = numbers[0]
        logger.debug(f"  Found phone number '{number}' in substitute '{substitute}'")

        for timeslot in re.split(r"(?:und)|,", substitute):
            logger.debug(f"  Processing timeslot '{timeslot}'")

            matches = regex_from_to.match(timeslot)
            if matches:
                # matches 12:30- 13:20 and 12:30 Uhr - 13:20 Uhr
                time_from, time_to = matches.group('from'),  matches.group('to')
                logger.debug(f"    Extracted timeslot '{time_from}' to '{time_to}'")
                rules.append({'time' : time_from, 'prefix' : "ab", 'pair' : pair_id, 'number' : number})
                rules.append({'time' : time_to, 'prefix': "bis", 'pair' : pair_id, 'number' : number})
                pair_id += 1
                continue

            
            matches = regex_from_or_to.match(timeslot)
            if matches:
                # Matches 'ab 13:20' or 'bis 13:20'
                prefix, time = matches.group('fromOrTo'), matches.group('time')
                logger.debug(f"    Extracted timeslot '{prefix}' '{time}'")
                if prefix == 'bis':
                    logger.debug(f"    Equivalent to '{shift_start}' '{time}'")
                    rules.append({'time' : shift_start, 'prefix' : 'ab', 'pair': None, 'number' : number})
                    rules.append({'time' : time, 'prefix' : 'bis', 'pair' : None, 'number' : number})
                    continue
                elif prefix == 'ab':
                    logger.debug(f"    Equivalent to '{time}' '{shift_end}'")
                    rules.append({'time' : time, 'prefix' : 'ab', 'pair': None, 'number' : number})
                    # rules.append({'time' : shift_end, 'prefix' : 'bis', 'pair' : None, 'number' : number})
                    continue
                raise Exception(f"Failed to parse timeslot '{timeslot}', this should never happen")

            logger.error(f"    Failed to parse timeslot '{timeslot}', make sure to use the format 'hh:mm - hh:mm' or 'ab hh:mm' or 'bis hh:mm'")

    if not any(rule['time'] == shift_start for rule in rules):
        rules.append({'time' : shift_start, 'prefix' : "ab", 'pair' : None, 'number' : default_number})

    rules = sorted(rules, key=lambda d: d['time'] + d['prefix'])

    # tricky: we have to translate the rules into a continuous list of intervals with the correct number for that interval
    # If we encouter a substitution ending rule, we need to change back to the previous number, so we need a stack to keep
    # track of the currently active numbers and take the most recent one of those

    # stack.pop, stack.append
    # stack.last()

    intervals = []
    stack = [{'pair': None, 'number': default_number}]
    for rule in rules:
        time = rule.pop('time')
        if rule.pop('prefix') == 'ab':
            stack.insert(0, rule)
        else: # bis
            if rule in stack:
                stack.remove(rule) # remove previously added 'ab' with same number & pair id

        intervals.append([time, stack[0]['number']])

    for i in range(len(intervals)-1):
        intervals[i].insert(1, intervals[i+1][0])
    intervals[-1].insert(1, shift_end)

    no_empty_intervals = filter(lambda interval: interval[0] != interval[1], intervals)
    return list(no_empty_intervals)
