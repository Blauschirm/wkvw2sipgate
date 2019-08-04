import requests
import json
import logging
from typing import List, Set, Dict, Tuple, Optional

class UserInfo(object):
    """
    Holds information about users (retrieved from the SIPGATE API).
    """
    def __init__(self, id : str, firstname : str, lastname : str, email : str):
        self.id = id
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
    
    def __str__(self):
        return f"[User ID={self.id} FirstName={self.firstname} LastName={self.lastname} Email={self.email}]"

class ApiCaller(object):
    """
    Wrapper for API calls, for better error handling, logging and a foundation for retries
    """

    def __init__(self, base_url: str, headers, logger=None):
        self.base_url = base_url
        self.headers = headers
        self.logger = logger   
        self.__logger = logging.getLogger(ApiCaller.__name__)

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
            self.__logger.error(e)
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
        response = self.__request('get', '/numbers')
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

        target_phone_numbers: Dict = {}
        for user in users: # todo get users
            response = self.__request('get', '/' + user.id + '/devices')
            for device_dict in response['items']:
                device_phone_number = device_dict.get('number')
                if not device_phone_number:
                    self.__logger.info(f"device {device_dict['id']} of user {user.lastname} ({user.id}) does not have a linked phone number")
                    continue

                if device_phone_number in target_phone_numbers:
                    if target_phone_numbers[device_phone_number]['userId'] != user.id:
                        self.__logger.warning(f"Number {device_phone_number} from user {user.id} was already target number of user {target_phone_numbers[device_phone_number]}. Skipping.")
                    else:
                        self.__logger.info(f"Number {device_phone_number} from user {user.id} is a duplicate.")
                    continue

                # saving userId and all active phone line ids under the target number. The phone lines are sorted by id (in length and value)
                target_phone_numbers[device_phone_number] = {'userId': user.id, 'activePhonelines': sorted(
                    device_dict['activePhonelines'], key=lambda ps: (len(ps['id']), ps['id']))}

        self.__logger.debug(f"Dictionary with target_numbers with their user's ids and active phone lines: {target_phone_numbers}")
            
        return target_phone_numbers
    
    def forward_outbound_to_private_phone_number(self, outbound_phone_number_id : str, private_phone_number_id : str) -> bool:
        return self.__request('put', '/numbers/' + outbound_phone_number_id, data=json.dumps({'endpointId': private_phone_number_id}))


class SipgateManager(object):
    """
    Establishes a connection to sipgate and allows to redirect public phone numbers to private ones.
    """
    
    def __init__(self, base_url: str, headers: dict, dryrun: bool = False):
        """
        Parameters
        ----------
        base_url
            Base URL of the SIPGATE API
        headers
            Headers to authenticated with SIPGATE
        dryrun
            If true `set_redirect_phone_number` does not actually reroute phone numbers 
            but just logs intended changes to WARNING.
        """
        self.__dryrun = dryrun
        self.__sipgate_api = ApiCaller(base_url, headers)
        self.__logger = logging.getLogger(SipgateManager.__name__)
        
        self.__logger.debug("Get all users")

        users = self.__sipgate_api.get_users()

        for user in users: 
            self.__logger.debug(f"Found user {user}")

        self.__private_phone_number_to_user_mapping = self.__sipgate_api.fetch_private_phone_number_to_user_mapping(users)

        for phone_number in self.__private_phone_number_to_user_mapping: 
            self.__logger.debug(f"Public phone number {phone_number} maps to private phone number {self.__private_phone_number_to_user_mapping[phone_number]}")

        self.__numbers = self.__sipgate_api.get_public_phone_numbers()

        self.__logger.debug(f"Dictionary with numbers and their ids and endpoints: {self.__numbers}")

    def set_redirect_phone_number(self, outbound_phone_number: str, redirect_phone_number: str) -> bool:
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
            outbund_number_id = self.__numbers[outbound_phone_number]['id']
        except:
            self.__logger.error(f"Desired outbund number '{outbound_phone_number}' not found via api. Make sure to use full number (+49...)")
            return False
        try:
            # Redirect calls to the outbund number to the first active phoneline connected with the targeted external phone number
            redirect_target_id = self.__private_phone_number_to_user_mapping[redirect_phone_number]['activePhonelines'][0]['id']
        except:
            self.__logger.error(f"Target phone number '{redirect_phone_number}' not found. Outbund number '{redirect_phone_number}' not rerouted")
            return False

        if not self.__dryrun:
            if self.__sipgate_api.forward_outbound_to_private_phone_number(outbund_number_id, redirect_target_id):
                self.__logger.info(f"Successfully rerouted outbund number '{outbound_phone_number}'({outbund_number_id})"
                    + f" to user device number '{redirect_phone_number}'(id: {redirect_target_id})")
                return True
            else:
                return False
        else:
            self.__logger.warning(f"[DRYRUN] Would have rerouted outbund number '{outbound_phone_number}'({outbund_number_id})"
                    + f" to user device number '{redirect_phone_number}'(id: {redirect_target_id}) otherwise.")
            return True

    def __str__(self):
        return f"[{SipgateManager.__name__}<{self.__sipgate_api.base_url}>]"