import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from guard.event import extract_command, load_event


class EventTests(unittest.TestCase):
    def test_extracts_command_from_tool_input(self):
        event = load_event('{"tool_input":{"command":"npm test"}}')
        self.assertEqual(extract_command(event), "npm test")

    def test_allows_empty_or_invalid_payloads(self):
        self.assertEqual(load_event(""), {})
        self.assertEqual(load_event("{nope"), {})
        self.assertEqual(extract_command({}), "")


if __name__ == "__main__":
    unittest.main()

