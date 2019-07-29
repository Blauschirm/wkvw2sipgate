import requests, json, re
from datetime import datetime
from bs4 import BeautifulSoup
import sipgate_api

# ToDo
# - Logging
# - E-Mails (mailgun)
#   - Fehlermeldungen auch schon für den nächsten Tag
#   - Bestätigung für (vielleicht nur virtuelle/dry-run) Umleitungen -> Simulationsfunktion
#       - config.jons: dryrun: Benutzt sipgate api nicht.
# - In Funktionen verpacken
#   - Tests
#   - config.json nur einmal gelesen wird, der rest wird dann injected
# - parser.py benutzen? Freitextfeld/Infofeld (i) auslesen und anwenden
# - Integrationstests
#   - Input: liste von datums, url, website
#   - Expected output: Liste von timeslots

# Set to true to use the testing accounts on sipgate and the local http server (make sure it's started)

with open('config.json', 'r') as config_file:
    config_data = json.load(config_file)

TESTING = config_data["TESTING"]
base_url = config_data["test_base_url" if TESTING else "real_base_url"]
login_payload = config_data["schedule_login_payload"]
#Nummern sind die Nummern des Test Accounts
NUMBER_MAP = config_data["NUMBER_MAP"]

def format_phone_number(number: str, nationalcode = '+49'):

    if number == None:
        return None
    
    # delete everything but digits, except for a '+' in the first position
    # [^0-9\+] matches every character that is not a digit or a + sign
    # (?!^)\+ matches all + signs that are not at at the start of the string
    new_number = re.sub(r"[^0-9\+]|(?!^)\+", "", number)
    # if after that the number is fully numeric, we need to add the +, maybe even the country code
    if new_number.isnumeric():
        new_number = new_number.lstrip('0')
        if new_number.find(nationalcode[1:]) == 0:
            # the nationalcode is already at the start of the number, assuming only the + sign is missing
            new_number = '+' + new_number
        else:
            new_number = nationalcode + new_number
    return new_number

errors = 0
warnings = 0

current_daytime_object = datetime.now()
current_day_of_month = current_daytime_object.day # Tag im Monat
current_hour_of_day = current_daytime_object.hour # Stunde des Tages

# Zwischen 0 und 8 Uhr ist die Schicht von Gestern dran
# ToDo am 1. jeden Monats müsste man die letzte Schicht vom letzten Monat betrachten
if current_hour_of_day < 8:
    current_day_of_month = current_day_of_month - 1

# take number of CARSTIS time script
if 8 <= current_hour_of_day < 20:
    first_shift = True
    second_shift = False
else:
    first_shift = False
    second_shift = True

# Da der Testserver kein Login fordert (und kein POST versteht), 
# reicht hier ein einfacher GET, für production wird die login_payload gebraucht
r = requests.get(base_url) if TESTING else requests.post(base_url, data=login_payload)
if not r.ok:
    raise Exception("Request to '{}' failed (HTTP Status Code {}): Text: {}".format(r.url, r.status_code, r.text))

soup = BeautifulSoup(r.text, features="html.parser")
# print(soup)

# class "tag" markiert die tage im Monat
all_days = soup.find_all(class_="tag")

# current_day_of_month ist immer der richtige tag
current_day = all_days[current_day_of_month]

day_row = current_day.parent

# Die drei Hauptspalten der aktuellen Zeile, also drei Leitungen separieren, die haben die Klasse "trenner"
Leitungen = day_row.find_all(class_="trenner")

NFS1 = Leitungen[0]
NFS2 = Leitungen[1]
Leitung = Leitungen[2]

# FRAGE: Warum hier href als selector? - P:href kommt anstatt span wenn es keinen eintrag gibt

nfs1_soup = NFS1.find_all(['span', 'href'])
nfs2_soup = NFS2.find_all(['span', 'href'])
leitung_soup = Leitung.find_all(['span', 'href'])
# test = leitung_soup[1]
# print(test.contents)

def AssignNumbersToTimeSlots(double_cell_soup, phone_line: str):
    global warnings
    if len(double_cell_soup) == 4:
        print('INFO: Two entries, one for each shift for line {}'.format(phone_line))
        
        FirstNumber = double_cell_soup[1]
        SecondNumber = double_cell_soup[3]
        slot1 = FirstNumber.contents[0]
        slot2 = SecondNumber.contents[0]
    elif len(double_cell_soup) == 2:
        print('WARNING: Only a single entry. Using the single entry for both shifts for line {}'.format(phone_line))
        warnings += 1

        FirstNumber = double_cell_soup[1]
        slot1 = FirstNumber.contents[0]
        slot2 = FirstNumber.contents[0]
    else:
        slot1 = None  # implement warning here
        slot2 = None

    return slot1, slot2  # give attribute of certain leitung

# AB HIER IST NOCH NICHT RICHTIG
[NFS1_Slot1, NFS1_Slot2] = AssignNumbersToTimeSlots(nfs1_soup, "nfs1")
[NFS2_Slot1, NFS2_Slot2] = AssignNumbersToTimeSlots(nfs2_soup, "nfs2")
[Leitung_Slot1, Leitung_Slot2] = AssignNumbersToTimeSlots(leitung_soup, "leitung")

redirects = {}

if first_shift:
    print('INFO: 1. shift selected')
    redirects['NFS1'] = format_phone_number(NFS1_Slot1)
    redirects['NFS2'] = format_phone_number(NFS2_Slot1)
    redirects['Leitung'] = format_phone_number(Leitung_Slot1)
elif second_shift:
    print('INFO: 2. shift selected')
    redirects['NFS1'] = format_phone_number(NFS1_Slot2)
    redirects['NFS2'] = format_phone_number(NFS2_Slot2)
    redirects['Leitung'] = format_phone_number(Leitung_Slot2)
else:
    raise Exception("Shift could not be determined")

# n1 = format_phone_number("+491637454")
# n2 = format_phone_number("01637454")
# n3 = format_phone_number("0163 / 7454")
# n4 = format_phone_number("+49 163 / 7454")
# n5 = format_phone_number("+49 163-7454")
# n6 = format_phone_number("+49+1637454")
# n7 = format_phone_number("0+1637454")
# n7 = format_phone_number("0491637454")

print("Redirects:", redirects)

for key, value in redirects.items():
    print("------------ Rerouting '{}' ------------".format(key))

    if not value: # Matches emptystring and None
        errors += 1
        print("ERROR: Key '{}' has no assigned phone number, forwarding stays unchanged".format(key))
        continue

    outbundnumber = format_phone_number(NUMBER_MAP[key])
    if not sipgate_api.set_redirect_target(outbundnumber, value):
        errors = errors + 1

print("Finished with {} error(s) and {} warning(s).".format(errors, warnings))