import pytest
import crawler, re
import phonenumbers

testdata = [
    (None, None),
    ("+491729394781", '+491729394781'),
    ('01729394781', '+491729394781'),
    ('Herr Müstermann mit +49 17 2 939 4781 ist jetzt dran', '+491729394781'),
    ('+49 17 2 939 4781!!++', '+491729394781'),
    ('00447746493918', '+447746493918'),
    ('+447746493918', '+447746493918'),
]

@pytest.mark.parametrize("given_phone_number, expected_phone_number", testdata)
def test_given_valid_number_returns_expected(given_phone_number, expected_phone_number):
    assert expected_phone_number == crawler.format_phone_number(given_phone_number)

@pytest.mark.parametrize("given_phone_number, expected_phone_number", testdata)
def test_phonenumberother(given_phone_number, expected_phone_number):
    
    matches = list(phonenumbers.PhoneNumberMatcher(given_phone_number, "DE"))

    if len(matches) == 0:
        assert expected_phone_number == None
        return

    if len(matches) > 1:
        raise Exception(f"Expected 0 or 1 phone numbers but found {len(matches)} in '{given_phone_number}': {str(map(lambda match: match.number, matches))}")

    match = matches[0]

    assert expected_phone_number == phonenumbers.format_number(match.number, phonenumbers.PhoneNumberFormat.E164)
