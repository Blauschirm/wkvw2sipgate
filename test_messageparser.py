import pytest
import messageparser

def test_parsers_result_against_expected_shift_sequence():  
    shift_start = "08:00"
    shift_end   = "20:00"
    default_number = "+49767676"

    test1 = "bis 12:00 Uhr +491231; ab 17:00 Uhr +467898; 13:30 Uhr - 14:15 Uhr, 14:30-14:45, ab 16:00 Uhr +472892; 16:00-16:20 +4934623"

    expected_intervals = [
        ['08:00', '12:00', ' +491231'],
        ['12:00', '13:30', '+49767676'],
        ['13:30', '14:15', ' +472892'],
        ['14:15', '14:30', '+49767676'],
        ['14:30', '14:45', ' +472892'],
        ['14:45', '16:00', '+49767676'],
        ['16:00', '16:20', ' +4934623'],
        ['16:20', '17:00', ' +472892'],
        ['17:00', '20:00', ' +467898']
    ]

    actual_intervals = messageparser.parse(shift_start, shift_end, default_number, test1)
    
    assert expected_intervals == actual_intervals
    # self.assertSequenceEqual(expected_intervals, actual_intervals)