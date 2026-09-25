import unittest
from datetime import datetime

from exif_time_parser import ExifTimeParser, ParseError


class TestParse(unittest.TestCase):
    def test_full_format_with_space(self):
        dt = ExifTimeParser.parse("2013:04:24 12:34:56")
        self.assertEqual(dt, datetime(2013, 4, 24, 12, 34, 56))

    def test_full_format_with_t_separator(self):
        dt = ExifTimeParser.parse("2013:04:24T12:34:56")
        self.assertEqual(dt, datetime(2013, 4, 24, 12, 34, 56))

    def test_date_only(self):
        dt = ExifTimeParser.parse("2013:04:24")
        self.assertEqual(dt, datetime(2013, 4, 24, 0, 0, 0))

    def test_strips_whitespace(self):
        dt = ExifTimeParser.parse("  2013:04:24 12:34:56  ")
        self.assertEqual(dt, datetime(2013, 4, 24, 12, 34, 56))

    def test_sub_seconds_short(self):
        # "12" means 0.12 s = 120000 microseconds
        dt = ExifTimeParser.parse("2013:04:24 12:34:56", sub_seconds="12")
        self.assertEqual(dt, datetime(2013, 4, 24, 12, 34, 56, 120000))

    def test_sub_seconds_six_digits(self):
        dt = ExifTimeParser.parse("2013:04:24 12:34:56", sub_seconds="123456")
        self.assertEqual(dt, datetime(2013, 4, 24, 12, 34, 56, 123456))

    def test_sub_seconds_too_long_truncates(self):
        # More than 6 digits: truncate, not round.
        dt = ExifTimeParser.parse("2013:04:24 12:34:56", sub_seconds="1234567")
        self.assertEqual(dt, datetime(2013, 4, 24, 12, 34, 56, 123456))

    def test_sub_seconds_none(self):
        dt = ExifTimeParser.parse("2013:04:24 12:34:56", sub_seconds=None)
        self.assertEqual(dt.microsecond, 0)

    def test_sub_seconds_empty_string(self):
        dt = ExifTimeParser.parse("2013:04:24 12:34:56", sub_seconds="")
        self.assertEqual(dt.microsecond, 0)

    def test_sub_seconds_whitespace_only(self):
        dt = ExifTimeParser.parse("2013:04:24 12:34:56", sub_seconds="   ")
        self.assertEqual(dt.microsecond, 0)

    def test_sub_seconds_single_digit(self):
        # "1" -> 0.1 s = 100000 microseconds
        dt = ExifTimeParser.parse("2013:04:24 12:34:56", sub_seconds="1")
        self.assertEqual(dt.microsecond, 100000)

    def test_invalid_month_raises(self):
        with self.assertRaises(ParseError):
            ExifTimeParser.parse("2013:13:24 12:34:56")

    def test_invalid_day_raises(self):
        with self.assertRaises(ParseError):
            ExifTimeParser.parse("2013:02:30 12:34:56")

    def test_garbage_raises(self):
        with self.assertRaises(ParseError):
            ExifTimeParser.parse("not a date")

    def test_empty_raises(self):
        with self.assertRaises(ParseError):
            ExifTimeParser.parse("")

    def test_wrong_type_raises(self):
        with self.assertRaises(ParseError):
            ExifTimeParser.parse(12345)  # type: ignore

    def test_bad_sub_seconds_raises(self):
        with self.assertRaises(ParseError):
            ExifTimeParser.parse("2013:04:24 12:34:56", sub_seconds="abc")

    def test_bad_sub_seconds_type_raises(self):
        with self.assertRaises(ParseError):
            ExifTimeParser.parse("2013:04:24 12:34:56", sub_seconds=12)

    def test_parse_error_is_value_error(self):
        with self.assertRaises(ValueError):
            ExifTimeParser.parse("bad")


class TestNormalize(unittest.TestCase):
    def test_full_to_iso(self):
        result = ExifTimeParser.normalize("2013:04:24 12:34:56")
        self.assertEqual(result, "2013-04-24T12:34:56")

    def test_with_sub_seconds(self):
        result = ExifTimeParser.normalize("2013:04:24 12:34:56", sub_seconds="12")
        self.assertEqual(result, "2013-04-24T12:34:56.120000")

    def test_date_only_normalizes(self):
        result = ExifTimeParser.normalize("2013:04:24")
        self.assertEqual(result, "2013-04-24T00:00:00")


if __name__ == "__main__":
    unittest.main()
