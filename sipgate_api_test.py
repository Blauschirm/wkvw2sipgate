import requests
from bs4 import BeautifulSoup

# Verbose logging
verbose = True

SIPGATE_PASS_BASE64 = "bWF4LmJvdHNjaGVuQGdtYWlsLmNvbTp2V3JNanJxNWVBdERSSkc="
SIPGATE_HEADERS = {'Authorization': 'Basic ' + SIPGATE_PASS_BASE64,
           'Accept': 'application/json', 'Content-Type': 'application/json'}
SIPGATE_BASE_URL = "https://api.sipgate.com/v2"

# Wrapper for API calls, for better error handling, logging and a foundation for retries
class ApiCaller(object):

    def __init__(self, base_url, headers, logger=None):
        self.base_url = base_url
        self.headers = headers
        self.logger = logger

    def request(self, method, relative_url, query_params=None, data=None, headers=None):
        headers = headers or self.headers
        try:
            response = requests.request(
                method, self.base_url + relative_url, params=query_params, data=data, headers=headers)
            response.raise_for_status()

            try:
                return response.json()
            except:
                return None

        except requests.exceptions.RequestException as e:
            # Log error e to log
            print(e)


sipgate_api = ApiCaller(SIPGATE_BASE_URL, SIPGATE_HEADERS)

if verbose:
    print("-> Get all users")

response = sipgate_api.request('get', "/app/users")

users = []

for item in response['items']:
    users.append({'id': item['id'], 'firstname': item['firstname'],
                  'lastname': item['lastname'], 'email': ['email']})

target_numbers = {}

# Get all target phone numbers of all users and link them to the users id
for user in users:
    response = sipgate_api.request('get',
                                   '/' + user['id'] + '/devices')
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
                print("device {} of user {} ({}) does not have a linked phone number".format(
                    device['id'], user['lastname'], user['id']))

if verbose:
    print("Dictionary with target_numbers and their user's ids: ", target_numbers)


def set_redirect_target(outbund_number, redirect_target):

    response = sipgate_api.request('put', '/numbers/24928181', data='{"endpointId" : "p0"}')


set_redirect_target(None, None)
