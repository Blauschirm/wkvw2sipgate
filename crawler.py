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

spans_wo_class = soup.find_all("td", class_="")
print(len(spans_wo_class))

now = datetime.datetime.now()  # Carsten
date = now.strftime("%d")  # Carsten
