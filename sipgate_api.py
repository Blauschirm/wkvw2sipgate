import requests
import json
from typing import List, Set, Dict, Tuple, Optional

# Verbose logging
verbose = True

with open('config.json', 'r') as config_file:
    config_data = json.load(config_file)

SIPGATE_BASE_URL = config_data["SIPGATE_BASE_URL"]
SIPGATE_PASS_BASE64 = config_data["SIPGATE_PASS_BASE64"]

SIPGATE_HEADERS = {'Authorization': 'Basic ' + SIPGATE_PASS_BASE64,
                   'Accept': 'application/json', 'Content-Type': 'application/json'}

class UserInfo(object):
    def __init__(self, id : str, firstname : str, lastname : str, email : str):
        self.id = id
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
    
    def __str__(self):
        return f"[User ID={self.id} FirstName={self.firstname} LastName={self.lastname} Email={self.email}]"

class PublicPhonenumber(object):
    def __init__(self, id : str, phone_number : str):
        self.id = id
        self.phone_number = phone_number

class ApiCaller(object):
    """
    Wrapper for API calls, for better error handling, logging and a foundation for retries
    """

    def __init__(self, base_url: str, headers, logger=None):
        self.base_url = base_url
        self.headers = headers
        self.logger = logger    

    def __request(self, http_method, relative_url, data=None, headers=None):
        """
        Parameters
        --------
        method : 'put' | 'get'
        relative_url : str
            The API endpoint to use, including the parameters.
        data : { endpointId: str }
        headers : {Authorization, Accept, content type}
        """
        headers = headers or self.headers
        try:
            response = requests.request(
                http_method, self.base_url + relative_url, data=data, headers=headers)
            response.raise_for_status()

            try:
                return response.json()
            except:
                return True

        except requests.exceptions.RequestException as e:
            # Log error e to log
            print(e)
            return False

    def get_users(self) -> List[UserInfo]:
        """
        Fetches the ids, first and last names and email address of the users.

        Returns
        -------
        ```
        UserInfo[]
        ```
        """
        response = self.__request('get', "/app/users") # todo 
        
        users:List[UserInfo] = []
        
        for item in response['items']:
            users.append(UserInfo(id = item['id'],
                firstname = item['firstname'],
                lastname = item['lastname'],
                email = item['email']))
        return users

    def get_public_phone_numbers(self):
        """
        Gets all public Numbers
        
        Returns
        -------
        ```
        {
            id: str,
            endpointId: str
        }
        ```
        """
        numbers = {}
        response = sipgate_api.__request('get', '/numbers')
        for item in response['items']:
            numbers[item['number']] = {'id': item['id']} # , 'endpointId': item['endpointId']} ToDo do we need the endpoint?
        
        return numbers

    def fetch_private_phone_number_to_user_mapping(self, users: List[UserInfo]):
        """
        Get all private numbers of all given users mapped to the user.

        Parameters
        ----------
        users: Users from ApiCaller.get_users()

        Returns
        -------
        Dictionary<privatePhonenumber, { userId, phoneLines: {id, alias}[] }>
        """

        # Get all target phone numbers of all users and link them to the users id

        # Device
        # - Type1: External phone with a phone number
        # - Type2: Sipgate sim card
        # - Type3: Sipgate VOIP

        target_phone_numbers = {}
        for user in users: # todo get users
            response = self.__request('get', '/' + user.id + '/devices')
            for device_dict in response['items']:
                device_phone_number = device_dict.get('number')
                if not device_phone_number:
                    if verbose:
                        print(f"device {device_dict['id']} of user {user.lastname} ({user.id}) does not have a linked phone number")
                    continue

                if device_phone_number in target_phone_numbers:
                    if target_phone_numbers[device_phone_number]['userId'] != user.id:
                        print(f"Warning! Number {device_phone_number} from user {user.id} was already target number of user {target_phone_numbers[device_phone_number]}. Skipping.")
                    else:
                        print(f"Warning! Number {device_phone_number} from user {user.id} was already entered.")
                    continue

                # saving userId and all active phone line ids under the target number. The phone lines are sorted by id (in length and value)
                target_phone_numbers[device_phone_number] = {'userId': user.id, 'activePhonelines': sorted(
                    device_dict['activePhonelines'], key=lambda ps: (len(ps['id']), ps['id']))}

        if verbose:
            print("Dictionary with target_numbers with their user's ids and active phone lines: ", target_phone_numbers)
            
        return target_phone_numbers
    
    def forward_outbound_to_private_phone_number(self, outbound_phone_number_id : str, private_phone_number_id : str) -> bool:
        return self.__request('put', '/numbers/' + outbound_phone_number_id, data=json.dumps({'endpointId': private_phone_number_id}))

sipgate_api = ApiCaller(SIPGATE_BASE_URL, SIPGATE_HEADERS)

if verbose:
    print("-> Get all users")

users = sipgate_api.get_users()

for user in users: 
    print("user", user)

private_phone_number_to_user_mapping = sipgate_api.fetch_private_phone_number_to_user_mapping(users)

for phone_number in private_phone_number_to_user_mapping: 
    print("ptu", phone_number, "->", private_phone_number_to_user_mapping[phone_number])

numbers = sipgate_api.get_public_phone_numbers()

if verbose:
    print("Dictionary with numbers and their ids and endpoints: ", numbers)

def set_redirect_phone_number(outbound_phone_number: str, redirect_phone_number: str):
    """
    Function to reroute outbound number to employees phone number
    returns True for success ans False for Failure

    Parameters
    ----------
        outbound_phone_number : str
            Public constant number which shall redirect to the redirect_phone_number.
        redirect_phone_number : str
            The number to redirect to.
    """
    try:
        outbund_number_id = numbers[outbound_phone_number]['id']
    except:
        print(f"ERROR: desired outbund number '{outbound_phone_number}' not found via api. Make sure to use full number (+49...)")
        return False
    try:
        # Redirect calls to the outbund number to the first active phoneline connected with the targeted external phone number
        redirect_target_id = private_phone_number_to_user_mapping[redirect_phone_number]['activePhonelines'][0]['id']
    except:
        print(f"ERROR: target phone number '{redirect_phone_number}' not found. Outbund number '{redirect_phone_number}' not rerouted")
        return False

    if sipgate_api.forward_outbound_to_private_phone_number(outbund_number_id, redirect_target_id):
        print(f"Successfully rerouted outbund number '{outbound_phone_number}'({outbund_number_id})\
                to user device number '{redirect_phone_number}'({redirect_target_id})")
        return True
    else:
        return False
