import requests, json, datetime, re
from bs4 import BeautifulSoup
import sipgate_api

with open('config.json', 'r') as config_file:
    config_data = json.load(config_file)

base_url = config_data["real_base_url"]
login_payload = config_data["schedule_login_payload"]
#Nummern sind die Nummern des Test Accounts
NUMBER_MAP = config_data["NUMBER_MAP"]

def format_phone_number(number, nationalcode = '+49'):

    if number == None:
        return None
    
    # delete everything but digits, except for a '+' in the first position
    # [^0-9\+] matches every character that is not a digit or a + sign
    # (?!^)\+ matches all + signs that are not at at the start of the string
    new_number = re.sub("[^0-9\+]|(?!^)\+", "", number)
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


now = datetime.datetime.now()  # Carsten
date = now.strftime("%d")  # Carsten, is ein string hier
date_int = int(date)  # day number, int("08") = 8, also kein problem hier
hour = now.hour  # Carsten :)))))
hour_int = int(hour)  # int hour, zb wenn es 22:36 ist ist hour = 22

# nummern für richtigen tag nehmen
if hour_int < 8:
    date_int = date_int - 1

# take number of CARSTIS time script
if 8 <= hour_int < 20:
    FirstSlot = True
    SecondSlot = False
else:
    FirstSlot = False
    SecondSlot = True

r = requests.post(base_url, data=login_payload)

soup = BeautifulSoup(r.text, features="html.parser")

# class "tag" markiert die tage im Monat
all_days = soup.find_all(class_="tag")

# date_int ist immer der richtige tag
current_day = all_days[date_int]

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
test = leitung_soup[1]
# print(test.contents)

def AssignNumbersToTimeSlots(double_cell_soup):

    if len(double_cell_soup) == 4:
        FirstNumber = double_cell_soup[1]
        SecondNumber = double_cell_soup[3]
        slot1 = FirstNumber.contents[0]
        slot2 = SecondNumber.contents[0]
    elif len(double_cell_soup) == 2:
        FirstNumber = double_cell_soup[1]
        slot1 = FirstNumber.contents[0]
        slot2 = FirstNumber.contents[0]
    else:
        slot1 = None  # implement warning here
        slot2 = None

    return slot1, slot2  # give attribute of certain leitung

# AB HIER IST NOCH NICHT RICHTIG
[NFS1_Slot1, NFS1_Slot2] = AssignNumbersToTimeSlots(nfs1_soup)
[NFS2_Slot1, NFS2_Slot2] = AssignNumbersToTimeSlots(nfs2_soup)
[Leitung_Slot1, Leitung_Slot2] = AssignNumbersToTimeSlots(leitung_soup)

redirects = {}

if FirstSlot:
    redirects['NFS1'] = format_phone_number(NFS1_Slot1)
    redirects['NFS2'] = format_phone_number(NFS2_Slot1)
    redirects['Leitung'] = format_phone_number(Leitung_Slot1)
elif SecondSlot:
    redirects['NFS1'] = format_phone_number(NFS1_Slot2)
    redirects['NFS2'] = format_phone_number(NFS2_Slot2)
    redirects['Leitung'] = format_phone_number(Leitung_Slot2)
else:
    print("ERROR: No timeslot could be determined!")

# n1 = format_phone_number("+491637454")
# n2 = format_phone_number("01637454")
# n3 = format_phone_number("0163 / 7454")
# n4 = format_phone_number("+49 163 / 7454")
# n5 = format_phone_number("+49 163-7454")
# n6 = format_phone_number("+49+1637454")
# n7 = format_phone_number("0+1637454")
# n7 = format_phone_number("0491637454")

print(redirects)


for key, value in redirects.items():
    if value != None:
        outbundnumber = format_phone_number(NUMBER_MAP[key])
        if not sipgate_api.set_redirect_target(outbundnumber, value):
            errors = errors + 1

print("Finished with {} error(s) and {} warning(s).".format(errors, warnings))
breakpoint()