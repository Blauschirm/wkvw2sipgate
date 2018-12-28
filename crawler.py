import requests
from bs4 import BeautifulSoup
import datetime

base_url = 'http://notfallplan-dortmund.notfallseelsorge-ekvw.de/?q=user%2Flogin&destination=rufbereitschaft'

login_payload = {
    'name': 'Pablo Gottheil',
    'pass': 'Auf&290794',
    # Preferably set your password in an env variable and sub it in.
    'form_id': 'user_login'
}

r = requests.post(base_url, data=login_payload)

soup = BeautifulSoup(r.text)


now = datetime.datetime.now()  # Carsten
date = now.strftime("%d")  # Carsten, is ein string hier 
date_int = int(date) # day number, int("08") = 8, also kein problem hier
hour= now.hour # Carsten :))))) 
hour_int = int(hour) # int hour, zb wenn es 22:36 ist ist hour = 22

#nummern für richtigen tag nehmen
if hour_int < 8:
    date_int = date_int - 1

# class "tag" markiert die tage im Monat
all_days = soup.find_all(class_="tag")

#take number of CARSTIS time script
if hour_int < 20 & hour_int > 8:
    FirstSlot = True
    SeconDSlot = False
else:
    FirstSlot = False
    SecondSlot = True

#date_int ist immer der richtige tag
current_day = all_days[date_int]

#3 leitungen teilen, trenner ist trenner :D

day_row = current_day.parent

Leitungen = day_row.find_all(class_= "trenner")


NFS1 = Leitungen[0]
NFS2 = Leitungen[1]
Leitung = Leitungen[2]

attr1 = NFS1.find_all(['span', 'href'])
attr2 = NFS2.find_all(['span', 'href'])
attr3 = Leitung.find_all(['span', 'href'])
test = attr3[1]
#print(test.contents)

def AssignNumbersToTimeSlots(attr1):
    if len(attr1) == 4:
        FirstNumber = attr1[1]
        SecondNumber = attr1[3]
        NFS1_Slot1 = FirstNumber.contents
        NFS1_Slot2 = SecondNumber.contents
    elif len(attr1) == 2:
        FirstNumber = attr1[1]
        NFS1_Slot1 = FirstNumber.contents
        NFS1_Slot2 = FirstNumber.contents
    else:
        NFS1_Slot1 = None #implement warning here
        NFS1_Slot2 = None
    return NFS1_Slot1, NFS1_Slot2#give attribute of certain leitung

# AB HIER IST NOCH NICHT RICHTIG
[NFS1_Slot1, NFS1_Slot2] = AssignNumbersToTimeSlots(attr1)

if FirstSlot == True:
    einseins
    zweieins
    dreieins

dictionary = {'NFS 1 (häuslich)': 123, 'NFS 2 (häuslich)':123 , 'Leitung': 123}

#print(NFS1_Slot1)