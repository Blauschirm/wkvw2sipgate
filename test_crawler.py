import pytest
import crawler, re
import phonenumbers

testdata = [
    (None, None),
    ("+491729394781", '+491729394781'),
    ('01729394781', '+491729394781'),
    ('Herr Müstermann mit +49 17 2 939 4781 ist jetzt dran', '+491729394781'),
    ('+49 17 2 939 4781!!++', '+491729394781'),
    ('Crazy+49s17t293r94n781g do we even want to support this???', '+491729394781'), # phonenumbers fails on this
    ('00447746493918', '+447746493918'),
    ('+447746493918', '+447746493918'),
]

@pytest.mark.parametrize("given_phone_number, expected_phone_number", testdata)
def test_format_phone_number_GivenPhoneNumberString_WhenFormatting_ThenReturnsExpected(given_phone_number, expected_phone_number):
    assert expected_phone_number == crawler.format_phone_number(given_phone_number)

@pytest.mark.parametrize("given_phone_number, expected_phone_number", testdata)
def test_format_phone_number_alternative_GivenPhoneNumberString_WhenParsingAndFormatting_ThenReturnsExpected(given_phone_number, expected_phone_number):
    """
    As an alternative to crawler.format_phone_number we could use the phonenumbers module!
    """
    def parse_and_format(phone_number_string: str, default_country: str = "DE"):
        matches = list(phonenumbers.PhoneNumberMatcher(phone_number_string, "DE"))

        if len(matches) == 0:
            assert expected_phone_number == None
            return

        if len(matches) > 1:
            raise Exception(f"Expected 0 or 1 phone numbers but found {len(matches)} in '{phone_number_string}': {str(map(lambda match: match.number, matches))}")

        return phonenumbers.format_number(matches[0].number, phonenumbers.PhoneNumberFormat.E164)

    assert expected_phone_number == parse_and_format(given_phone_number)
