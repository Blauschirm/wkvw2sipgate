import re

def parse(schicht_anfang, schicht_ende, default_number, text_content):
    """
    Returns a list of time intervals with the given phone number for the interval, according to a string with correct formatting
    all times are handled as "24:00" strings

    # Format: Uhrzeiten immer mit Doppelpunkt und Minuten als hh:mm
    # Zeitintervalle mit Bindestrich kennen "-". Leerzeichen sind optional.
    # offene Angaben mit Schlüsselwoertern "bis" und "ab" vor der Uhrzeit. Gilt ab oder bis Schichtende oder -Anfang.
    # Telefonnummern ohne Sonder- oder Leerzeichen.
    # Verschiedene Vetretungen mit Semikolon trennen ";"
    # Verschachtelte und überlappende Vertretungen sind nicht möglich!
    # Mehrere Uhrzeitbereiche für die selbe Vertretung können mit Komma und "und" aneinander gereiht werden.
    # Beispiel: "bis 10:00 Uhr +491234; bis 12:20, 13:00-14:20 und ab 17:00 Uhr +494321"

    Parameters:
    schicht_anfang (string): regular beginning of shift
    schicht_ende   (string): regular end of shift
    default_number (string): regular phone number for this shift
    text_content   (string): content of the comment box, which gets parsed into the substitution rules 

    Returns:
    intervals      (list of lists): list of lists with format [interval_start, interval_end, phone_number]
    """
    # pad all hours, 9:12 -> 09:12 
    text_content = text_content.lower()
    re.sub(r"(?<=\D)(\d:\d\d)", r"0\1", text_content)
    rules = []
    pair_id = 1

    for substitute in text_content.split(';'):
        numbers = re.findall(r"(?:\s)\+?\d{5,}", substitute)
        if len(numbers) != 1:
            print("ERROR! Not exactly one telephone number per substitute segment!")
            continue 
        else:
            number = numbers[0]
        for timeslot in re.split(r"(?:und)|,", substitute):
            valid_time_re = r"\d{1,2}\:\d\d"
            times = re.findall(valid_time_re, timeslot)

            if len(times) not in (1, 2):
                if len(times) > 2:
                    print("ERROR! To many times without a comma! Segment: " + str(timeslot))
                continue
            elif len(times) == 1:
                time = times[0]
                # Find all prefixes related to this time in this substitute segment
                # If the time get mentioned with different prefixes we have a conflict and skip this timeslot
                prefixes = re.findall(r"((?:bis)|(?:ab))\s*(?=" + time + r")", substitute)
                if len(set(prefixes)) == 1:
                    prefix = prefixes[0]
                    rules.append({'time' : time, 'prefix' : prefix, 'pair' : None, 'number' : number})
                    if prefix == 'bis':
                        rules.append({'time' : schicht_anfang, 'prefix' : 'ab', 'pair': None, 'number' : number})
                else:
                    print("ERROR! Conflicting prefixes for same time! Ignoring Segment: " + str(timeslot))
            elif len(times) == 2 and re.match(r".*" + valid_time_re + r"\s*(?:uhr)?\s*-\s*" +  valid_time_re, timeslot):
                # matches 12:30- 13:20 and 12:30 Uhr - 13:20 Uhr
                rules.append({'time' : times[0], 'prefix' : "ab", 'pair' : pair_id, 'number' : number})
                rules.append({'time' : times[1], 'prefix': "bis", 'pair' : pair_id, 'number' : number})
                pair_id += 1
            else:
                print("ERROR! Too many rules in one segment. Seperate rules by comma or 'und'. Ignoring Segment: " + str(timeslot))

    if not any(rule['time'] == schicht_anfang for rule in rules):
        rules.append({'time' : schicht_anfang, 'prefix' : "ab", 'pair' : None, 'number' : default_number})

    rules = sorted(rules, key=lambda d: d['time'] + d['prefix'])

    # tricky: we have to translate the rules into a continuous list of intervals with the correct number for that interval
    # If we encouter a substitution ending rule, we need to change back to the previous number, so we need a stack to keep
    # track of the currently active numbers and take the most recent one of those

    intervals = []
    stack = [{'pair': None, 'number': default_number}]
    for rule in rules:
        time = rule.pop('time')
        if rule.pop('prefix') == 'ab':
            stack.insert(0, rule)
        else:
            if rule in stack:
                stack.remove(rule)

        intervals.append([time, stack[0]['number']])

    for i in range(len(intervals)):
        if i+1 < len(intervals):
            intervals[i].insert(1, intervals[i+1][0])
        else:
            intervals[i].insert(1, schicht_ende)

    return intervals

if (__name__ == "__main__"):
    schicht_anfang = "09:00"
    schicht_ende   = "18:00"
    default_number = "+49767676"

    test1 = "bis 12:00 Uhr +491231; ab 17:00 Uhr +467898; 13:30 Uhr - 14:15 Uhr, 14:30-14:45, ab 16:00 Uhr +472892; 16:00-16:20 +4934623"

    intervals = parse(schicht_anfang, schicht_ende, default_number, test1)
    print("intervals:")
    for line in intervals:
        print(line)