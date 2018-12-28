import requests
from bs4 import BeautifulSoup

# Verbose logging
verbose = True

SIPGATE_PASS_BASE64 = "bWF4LmJvdHNjaGVuQGdtYWlsLmNvbTp2V3JNanJxNWVBdERSSkc="
# SIPGATE_HEADER = "Authorization: Basic " + SIPGATE_PASS_BASE64
headers = {'Authorization': 'Basic ' + SIPGATE_PASS_BASE64,
           'Accept': 'application/json', 'Content-Type': 'application/json'}
apiUrl = "https://api.sipgate.com/v2"

#   https://api.sipgate.com/v2/app/users Listet alle User mit id und email und so
#   https://api.sipgate.com/v2/{userId}/devices /Listet alle devices zu User
#

if verbose:
    print("-> Get all users")
response = requests.get(apiUrl + "/app/users", headers=headers).json()

users = []

for item in response['items']:
    users.append({'id': item['id'], 'firstname': item['firstname'],
                  'lastname': item['lastname'], 'email': ['email']})

target_numbers = {}

# Get all target phone numbers of all users and link them to the users id
for user in users:
    response = requests.get(
        apiUrl + '/' + user['id'] + '/devices', headers=headers).json()
    for device in response['items']:
        if 'number' in device:
            if device['number'] in target_numbers:
                if target_numbers[device['number']] != user['id']:
                    print("Warning! Number {} from user {} is already target number of user {}. Overwriting.".format(
                        device['number'], user['id'], target_numbers[device['number']]))
            else:
                target_numbers[device['number']] = user['id']
        else:
            if verbose:
                print("device {} of user {} does not have a linked phone number".format(
                    device['id'], user['id']))

if verbose:
    print("Dictionary with target_numbers and their user's ids: ", target_numbers)


def set_redirect_target(outbund_number, redirect_target):

    response = requests.put(apiUrl + '/numbers/24928181', headers=headers,
                            data='{"endpointId" : "p10", "releaseForMnp" : "false", "quickDial" : "false"}')
    print(response.text)


set_redirect_target(None, None)
