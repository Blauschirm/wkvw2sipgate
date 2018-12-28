import requests
from bs4 import BeautifulSoup

POSTLOGINURL = 'http://notfallplan-dortmund.notfallseelsorge-ekvw.de/?q=user%2Flogin&destination=rufbereitschaft'

#This URL is the page you actually want to pull down with requests.
REQUESTURL = 'https://l.facebook.com/l.php?u=http%3A%2F%2Fnotfallplan-dortmund.notfallseelsorge-ekvw.de%2F%3Fq%3Drufbereitschaft&h=AT22b8Rw6vcebg_I0HLuoTBUDX1tG0n8Ao6SC-BmKfdjncJJDZSIUisrmH8Qdnaj00WQAEMPDP6mg3AqYokwe90YXHBQrMqtwiPJpqkvFqyVUGqaSBcqWzR2scUqTV8kahRtbDwW'

s=requests.request('Get',POSTLOGINURL)
print(s)
#username-input-name is the "name" tag associated with the username input field of the login form.
#password-input-name is the "name" tag associated with the password input field of the login form.
payload = {
    'name': 'Pablo Gottheil',
    'pass': 'Auf&290794',
    'form_id':'user_login'#Preferably set your password in an env variable and sub it in.
}
soulstring="hii"
with requests.Session() as session:
    post = session.post(POSTLOGINURL, data=payload)
    url_to_scrape = 'http://notfallplan-dortmund.notfallseelsorge-ekvw.de/?q=rufbereitschaft'
    soulstring=post.text
    soup=BeautifulSoup(soulstring,"lxml")
