"""
自动化测试 - parse_duration days 单位支持
题目: [BOUNTY $50] parse_duration drops the days (d) unit
"""

import unittest
from datetime import timedelta

from solution import parse_duration, parse_duration_to_seconds


class TestParseDuration(unittest.TestCase):
    def test_days_only(self):
        self.assertEqual(parse_duration("2d"), timedelta(days=2))

    def test_hours_only(self):
        self.assertEqual(parse_duration("3h"), timedelta(hours=3))

    def test_minutes_only(self):
        self.assertEqual(parse_duration("30m"), timedelta(minutes=30))

    def test_seconds_only(self):
        self.assertEqual(parse_duration("45s"), timedelta(seconds=45))

    def test_combined(self):
        self.assertEqual(
            parse_duration("2d3h30m"),
            timedelta(days=2, hours=3, minutes=30),
        )

    def test_days_and_seconds(self):
        self.assertEqual(
            parse_duration("1d5s"),
            timedelta(days=1, seconds=5),
        )

    def test_fractional_days(self):
        self.assertEqual(parse_duration("0.5d"), timedelta(hours=12))

    def test_to_seconds(self):
        self.assertEqual(parse_duration_to_seconds("2d"), 172800.0)
        self.assertEqual(parse_duration_to_seconds("1h30m"), 5400.0)

    def test_invalid_input(self):
        self.assertIsNone(parse_duration(""))
        self.assertIsNone(parse_duration("abc"))
        self.assertIsNone(parse_duration("2x"))  # 未知单位
        self.assertIsNone(parse_duration(None))

    def test_whitespace_tolerant(self):
        self.assertEqual(
            parse_duration("2d 3h"),
            timedelta(days=2, hours=3),
        )


if __name__ == "__main__":
    unittest.main()
