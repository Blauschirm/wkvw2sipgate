import requests
from bs4 import BeautifulSoup

# Verbose logging
verbose = False

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
                return True

        except requests.exceptions.RequestException as e:
            # Log error e to log
            print(e)
            return False


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
            if device['number'] in target_numbers and target_numbers[device['number']]['userId'] != user['id']:
                print("Warning! Number {} from user {} was already target number of user {}. Overwriting.".format(
                    device['number'], user['id'], target_numbers[device['number']]))

            # saving userId and all active phone line ids under the target number. The phone lines are sorted by id (in length and value)
            target_numbers[device['number']] = {'userId': user['id'], 'activePhonelines': sorted(device['activePhonelines'],
                                                                                                 key=lambda ps: (len(ps['id']), ps['id']))}

        else:
            if verbose:
                print("device {} of user {} ({}) does not have a linked phone number".format(
                    device['id'], user['lastname'], user['id']))

if verbose:
    print("Dictionary with target_numbers with their user's ids and active phone lines: ", target_numbers)

if verbose:
    print("-> Get all numbers")
numbers = {}
response = sipgate_api.request('get', '/numbers')
for item in response['items']:
    numbers[item['number']] = {'id': item['id'],
                               'endpointId': item['endpointId']}
if verbose:
    print("Dictionary with numbers and their ids and endpoints: ", numbers)


# Function to reroute outbound number to employees phone number
# returns True for success ans False for Failure
def set_redirect_target(outbund_number, redirect_target):
    try:
        outbund_number_id = numbers[outbund_number]['id']
    except:
        print("ERROR: desired outbund number {} not found via api. Make sure to use full number (+49...)".format(outbund_number))
        return False
    try:
        # Redirect calls to the outbund number to the first active phoneline connected with the targeted external phone number
        redirect_target_id = target_numbers[redirect_target]['activePhonelines'][0]['id']
    except:
        print("ERROR: target phone number {} not found. Outbund number {} not rerouted".format(
            redirect_target, outbund_number))

        return False

    if sipgate_api.request('put', '/numbers/' + outbund_number_id, data='{"endpointId": "' + redirect_target_id + '"}'):
        print("Successfully rerouted outbund number {} to user device number {}".format(
            outbund_number, redirect_target))
        return True
    else:
        return False
