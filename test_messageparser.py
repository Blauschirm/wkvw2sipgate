import pytest
import messageparser

def test_TimeRule_sort_GivenSameTime_SortsByFromOrTill_And_PersistsRelativeOrder():
    rules = [
        messageparser.TimeRule(time="08:00", from_or_till=messageparser.FromOrTill.FROM, pair_id=1, phone_number="0"),
        messageparser.TimeRule(time="08:00", from_or_till=messageparser.FromOrTill.TILL, pair_id=2, phone_number="1"),
        messageparser.TimeRule(time="08:00", from_or_till=messageparser.FromOrTill.FROM, pair_id=3, phone_number="2"),
    ]
    expected_order = [rules[0], rules[2], rules[1]]
    assert expected_order == messageparser.TimeRule.sort(rules)

def test_TimeRule_sort_GivenDifferentTimes_SortsByTimeAndFromOrTill():
    rules = [
        messageparser.TimeRule(time="09:42", from_or_till=messageparser.FromOrTill.FROM, pair_id=1, phone_number="0"),
        messageparser.TimeRule(time="09:37", from_or_till=messageparser.FromOrTill.TILL, pair_id=3, phone_number="1"),
        messageparser.TimeRule(time="10:00", from_or_till=messageparser.FromOrTill.TILL, pair_id=2, phone_number="2"),
        messageparser.TimeRule(time="09:37", from_or_till=messageparser.FromOrTill.FROM, pair_id=3, phone_number="3"),
    ]
    expected_order = [rules[3], rules[1], rules[0], rules[2]]
    assert expected_order == messageparser.TimeRule.sort(rules)

def test_parse_rules_from_message():  
    shift_start = "08:00"
    shift_end   = "20:00"
    default_number = "+49767676"

    test_message = "bis 12:00 Uhr +491231; ab 17:00 Uhr +467898; 13:30 Uhr - 14:15 Uhr, 14:30-14:45, ab 16:00 Uhr +472892; 16:00-16:20 +4934623"

    expected_rules = [
        messageparser.TimeRule(time="08:00", from_or_till=messageparser.FromOrTill.FROM, pair_id=None, phone_number="+491231"),
        messageparser.TimeRule(time="12:00", from_or_till=messageparser.FromOrTill.TILL, pair_id=None, phone_number="+491231"),
        messageparser.TimeRule(time="13:30", from_or_till=messageparser.FromOrTill.FROM, pair_id=1, phone_number="+472892"),
        messageparser.TimeRule(time="14:15", from_or_till=messageparser.FromOrTill.TILL, pair_id=1, phone_number="+472892"),
        messageparser.TimeRule(time="14:30", from_or_till=messageparser.FromOrTill.FROM, pair_id=2, phone_number="+472892"),
        messageparser.TimeRule(time="14:45", from_or_till=messageparser.FromOrTill.TILL, pair_id=2, phone_number="+472892"),
        messageparser.TimeRule(time="16:00", from_or_till=messageparser.FromOrTill.FROM, pair_id=None, phone_number="+472892"),
        messageparser.TimeRule(time="16:00", from_or_till=messageparser.FromOrTill.FROM, pair_id=3, phone_number="+4934623"),
        messageparser.TimeRule(time="16:20", from_or_till=messageparser.FromOrTill.TILL, pair_id=3, phone_number="+4934623"),
        messageparser.TimeRule(time="17:00", from_or_till=messageparser.FromOrTill.FROM, pair_id=None, phone_number="+467898"),
        messageparser.TimeRule(time="20:00", from_or_till=messageparser.FromOrTill.TILL, pair_id=None, phone_number="+467898"),
        messageparser.TimeRule(time="20:00", from_or_till=messageparser.FromOrTill.TILL, pair_id=None, phone_number="+472892"),
    ]

    actual_rules = messageparser.parse_rules_from_message(shift_start, shift_end, default_number, test_message)

    assert expected_rules == actual_rules

def test_time_rules_to_interval_list():  
    shift_end = "20:00"
    default_number = "+49767676"

    rules = [
        messageparser.TimeRule(time="08:00", from_or_till=messageparser.FromOrTill.FROM, pair_id=None, phone_number="+491231"),
        messageparser.TimeRule(time="12:00", from_or_till=messageparser.FromOrTill.TILL, pair_id=None, phone_number="+491231"),
        messageparser.TimeRule(time="13:30", from_or_till=messageparser.FromOrTill.FROM, pair_id=1, phone_number="+472892"),
        messageparser.TimeRule(time="14:15", from_or_till=messageparser.FromOrTill.TILL, pair_id=1, phone_number="+472892"),
        messageparser.TimeRule(time="14:30", from_or_till=messageparser.FromOrTill.FROM, pair_id=2, phone_number="+472892"),
        messageparser.TimeRule(time="14:45", from_or_till=messageparser.FromOrTill.TILL, pair_id=2, phone_number="+472892"),
        messageparser.TimeRule(time="16:00", from_or_till=messageparser.FromOrTill.FROM, pair_id=None, phone_number="+472892"),
        messageparser.TimeRule(time="16:00", from_or_till=messageparser.FromOrTill.FROM, pair_id=3, phone_number="+4934623"),
        messageparser.TimeRule(time="16:20", from_or_till=messageparser.FromOrTill.TILL, pair_id=3, phone_number="+4934623"),
        messageparser.TimeRule(time="17:00", from_or_till=messageparser.FromOrTill.FROM, pair_id=None, phone_number="+467898"),
        messageparser.TimeRule(time="20:00", from_or_till=messageparser.FromOrTill.TILL, pair_id=None, phone_number="+467898"),
        messageparser.TimeRule(time="20:00", from_or_till=messageparser.FromOrTill.TILL, pair_id=None, phone_number="+472892"),
    ]

    expected_intervals = [
        ['08:00', '12:00', '+491231'],
        ['12:00', '13:30', '+49767676'],
        ['13:30', '14:15', '+472892'],
        ['14:15', '14:30', '+49767676'],
        ['14:30', '14:45', '+472892'],
        ['14:45', '16:00', '+49767676'],
        ['16:00', '16:20', '+4934623'],
        ['16:20', '17:00', '+472892'],
        ['17:00', '20:00', '+467898']
    ]

    actual_intervals = messageparser.time_rules_to_interval_list(rules, default_number, shift_end)
    
    assert expected_intervals == actual_intervals