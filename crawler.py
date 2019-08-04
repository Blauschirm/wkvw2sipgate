import requests, json, re, logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from sipgate_api import SipgateManager

logger = logging.getLogger('crawler')
warnings, errors = 0, 0

def format_phone_number(phone_number: str, country_code: str = '+49'):
    """
    Extracts the phone number from `phone_number`, removing all special characters.
    If it is not prefixed with a country calling code, it is prefixed with `country_code`.
    """

    if phone_number == None:
        return None
    
    # delete everything but digits, except for a '+' in the first position
    # [^0-9\+] matches every character that is not a digit or a + sign
    # (?!^)\+ matches all + signs that are not at at the start of the string
    new_phone_number = re.sub(r"[^0-9\+]|(?!^)\+", "", phone_number)
    # if after that the number is fully numeric, we need to add the +, maybe even the country code
    if new_phone_number.isnumeric():
        new_phone_number = new_phone_number.lstrip('0')
        if new_phone_number.find(country_code[1:]) == 0:
            # the nationalcode is already at the start of the number, assuming only the + sign is missing
            new_phone_number = '+' + new_phone_number
        else:
            new_phone_number = country_code + new_phone_number
    return new_phone_number

def fetch_shift_schedule_entries(base_url, login_payload, is_first_shift, target_daytime_object):
    """
    Parameters:
    base_url (string): regular beginning of shift
    login_payload   (string): regular end of shift
    day_of_month (string): regular phone number for this shift

    Returns:
    ```
    {
        NFS1: str,
        NFS2: str,
        Leitung: str    
    }
    ```
    """

    # Da der Testserver kein Login fordert (und kein POST versteht), 
    # reicht hier ein einfacher GET, für production wird die login_payload gebraucht

    relative_date_url = datetime.strftime(target_daytime_object, "%Y-%m") # YYYY-mm
    url = base_url + relative_date_url

    logger.debug(f"Connecting to shift-server at {url}")
    r = requests.get(url) if TESTING else requests.post(url, data=login_payload)
    if not r.ok:
        raise Exception("Request to '{}' failed (HTTP Status Code {}): Text: {}".format(r.url, r.status_code, r.text))

    soup = BeautifulSoup(r.text, features="html.parser")
    # print(soup)

    # class "tag" markiert die tage im Monat
    all_days = soup.find_all(class_="tag")

    # current_day_of_month ist immer der richtige tag
    current_day = all_days[target_daytime_object.day]

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

    # AB HIER IST NOCH NICHT RICHTIG
    [NFS1_Slot1, NFS1_Slot2] = AssignNumbersToTimeSlots(nfs1_soup, "nfs1")
    [NFS2_Slot1, NFS2_Slot2] = AssignNumbersToTimeSlots(nfs2_soup, "nfs2")
    [Leitung_Slot1, Leitung_Slot2] = AssignNumbersToTimeSlots(leitung_soup, "leitung")

    redirects = {}

    if is_first_shift:
        logger.info('1. shift selected')
        redirects['NFS1'] = format_phone_number(NFS1_Slot1)
        redirects['NFS2'] = format_phone_number(NFS2_Slot1)
        redirects['Leitung'] = format_phone_number(Leitung_Slot1)
    else:
        logger.info('2. shift selected')
        redirects['NFS1'] = format_phone_number(NFS1_Slot2)
        redirects['NFS2'] = format_phone_number(NFS2_Slot2)
        redirects['Leitung'] = format_phone_number(Leitung_Slot2)

    return redirects


def AssignNumbersToTimeSlots(double_cell_soup, phone_line: str):
    global warnings, logger
    if len(double_cell_soup) == 4:
        logger.info(f'Two entries, one for each shift for line {phone_line}')
        
        FirstNumber = double_cell_soup[1]
        SecondNumber = double_cell_soup[3]
        slot1 = FirstNumber.contents[0]
        slot2 = SecondNumber.contents[0]
    elif len(double_cell_soup) == 2:
        logger.warning(f'Only a single entry. Using the single entry for both shifts for line {phone_line}')
        warnings += 1

        FirstNumber = double_cell_soup[1]
        slot1 = FirstNumber.contents[0]
        slot2 = FirstNumber.contents[0]
    else:
        slot1 = None  # implement warning here
        slot2 = None

    return slot1, slot2  # give attribute of certain leitung

def determine_target_date(nextday = False):
    """
    Gives the current datetime object, or the one from yesterday if the previous days nightshift is required.
    If nextday == True, the next day will be fetched.
    
    Parameters
    ----------
    nextday: bool

    Returns
    -------
    <daytime oject>
    """
    target_daytime_object = datetime.now() + timedelta(days=int(nextday))
    # Zwischen 0 und 8 Uhr ist die Schicht von Gestern dran
    # ToDo am 1. jeden Monats müsste man die letzte Schicht vom letzten Monat betrachten
    if target_daytime_object.hour < 8:
        target_daytime_object = target_daytime_object - timedelta(days=1)
    logger.debug(f"target datetime is {datetime.strftime(target_daytime_object, '%d.%m.%Y %H:%M')}")
    return target_daytime_object

def make_redirects(sipgate_base_url, sipgate_headers, number_map, redirects, dryrun):
    global warnings, errors, logger
    sipgate_manager = SipgateManager(sipgate_base_url, sipgate_headers, dryrun)

    for key, private_phone_number in redirects.items():
        logger.info(f"------------ Rerouting '{key}' ------------")

        if not private_phone_number: # Matches emptystring and None
            errors += 1
            logger.error(f"Key '{key}' has no assigned phone number, forwarding stays unchanged")
            continue

        outbundnumber = format_phone_number(number_map[key])
        if not sipgate_manager.set_redirect_phone_number(outbundnumber, private_phone_number):
            errors = errors + 1


def fetch_and_apply_redirects(base_url: str, login_payload: str, dryrun: bool, nextday: bool = False):
    target_daytime_object = determine_target_date(nextday)

    is_first_shift = (8 <= target_daytime_object.hour < 20)
    # is_second_shift = not is_first_shift

    redirects = fetch_shift_schedule_entries(base_url, login_payload, is_first_shift, target_daytime_object)
    logger.info(f"Redirects: {redirects}")

    make_redirects(SIPGATE_BASE_URL, SIPGATE_HEADERS, NUMBER_MAP, redirects, dryrun)

    if errors or warnings:
        logger.warning(f"Finished with {errors} error(s) and {warnings} warning(s).")
    else:
        logger.info("Success. Finished without errors or warnings")


if __name__ == "main":
    with open('config.json', 'r') as config_file:
        config_data = json.load(config_file)

    TESTING = config_data["TESTING"]
    base_url = config_data["test_base_url" if TESTING else "real_base_url"]
    login_payload = config_data["schedule_login_payload"]
    NUMBER_MAP = config_data["NUMBER_MAP"]
    SIPGATE_BASE_URL = config_data["sipgate"]["base_url"]
    SIPGATE_HEADERS = {'Authorization': 'Basic ' + config_data["sipgate"]["pass_base64"],
                    'Accept': 'application/json', 'Content-Type': 'application/json'}
    dryrun = config_data["sipgate"]["dryrun"]

    logger.info(f"Test mode is {'enabled' if TESTING else 'disabled'}")

    errors = 0
    warnings = 0

    fetch_and_apply_redirects(base_url, login_payload, dryrun, nextday=False)
    fetch_and_apply_redirects(base_url, login_payload, dryrun, nextday=True)