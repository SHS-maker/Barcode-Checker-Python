import itertools
import unittest

from barcode_checker.core import (
    ScanSession, ScanState, barcodes_match, differing_indices,
    highlight_ranges, matches_with_one_extra_zero, normalize_scan,
)
from barcode_checker.settings import Settings


class ComparisonTests(unittest.TestCase):
    def test_exact_and_case_sensitive(self):
        self.assertTrue(barcodes_match("00123", "00123", False, False))
        self.assertFalse(barcodes_match("ABC", "abc"))
        self.assertFalse(barcodes_match("123", "321"))

    def test_contains_setting_in_both_directions(self):
        for a, b in (("123", "X123Y"), ("X123Y", "123")):
            self.assertTrue(barcodes_match(a, b, True, False))
            self.assertFalse(barcodes_match(a, b, False, False))

    def test_zero_can_be_inserted_anywhere(self):
        for longer in ("0123", "1023", "1203", "1230"):
            for a, b in (("123", longer), (longer, "123")):
                self.assertTrue(barcodes_match(a, b, False, True))
                self.assertFalse(barcodes_match(a, b, False, False))
        self.assertFalse(barcodes_match("123", "10023", False, True))
        self.assertFalse(barcodes_match("123", "1243", False, True))
        self.assertFalse(matches_with_one_extra_zero("0123", "123"))

    def test_tolerance_flags_independent(self):
        self.assertTrue(barcodes_match("123", "X123Y", True, False))
        self.assertFalse(barcodes_match("123", "1023", True, False))
        self.assertTrue(barcodes_match("123", "1023", False, True))

    def test_highlights_only_inserted_or_replaced_characters(self):
        self.assertEqual(differing_indices("12345", "12X345"), (set(), {2}))
        self.assertEqual(differing_indices("ABC", "AXC"), ({1}, {1}))
        self.assertEqual(differing_indices("ABC", "AB"), ({2}, set()))
        self.assertEqual(differing_indices("AB", "BA"), ({0}, {1}))
        self.assertEqual(differing_indices("", "ABC"), (set(), {0, 1, 2}))

    def test_lcs_against_exhaustive_subsequence_oracle(self):
        # Independent oracle verifies optimality, not another DP implementation.
        def subsequences(text):
            return {"".join(text[i] for i in range(len(text)) if mask & (1 << i))
                    for mask in range(1 << len(text))}
        words = ["".join(chars) for length in range(5)
                 for chars in itertools.product("01", repeat=length)]
        for a, b in itertools.product(words, repeat=2):
            da, db = differing_indices(a, b)
            kept_a = "".join(c for i, c in enumerate(a) if i not in da)
            kept_b = "".join(c for i, c in enumerate(b) if i not in db)
            self.assertEqual(kept_a, kept_b)
            self.assertEqual(len(kept_a), max(map(len, subsequences(a) & subsequences(b))))

    def test_highlight_ranges_use_java_utf16_and_coalesce(self):
        self.assertEqual(list(highlight_ranges("ABCDE", {1, 2, 4})), [(1, 3), (4, 5)])
        self.assertEqual(list(highlight_ranges("A😀BC", {1, 2})), [(1, 4)])
        self.assertEqual(list(highlight_ranges("ABC", set())), [])


class ScanTests(unittest.TestCase):
    def setUp(self):
        self.session = ScanSession()
        self.settings = Settings()

    def test_empty_scan_does_not_advance(self):
        for raw in ("", " ", "\r\n", "\t"):
            self.assertIsNone(self.session.consume(raw, self.settings))
        self.assertIs(self.session.state, ScanState.WAITING_BARCODE1)

    def test_two_scans_then_ignore_until_reset(self):
        self.session.consume(" 00123\r\n", self.settings)
        self.assertEqual(self.session.barcode1, "00123")
        self.assertIs(self.session.state, ScanState.WAITING_BARCODE2)
        result = self.session.consume("00123\n", self.settings)
        self.assertTrue(result.match)
        self.assertIs(self.session.state, ScanState.SHOWING_RESULT)
        self.assertIsNone(self.session.consume("different", self.settings))
        self.assertEqual(self.session.result, result)
        self.session.reset()
        self.assertIsNone(self.session.barcode1)
        self.assertIsNone(self.session.result)
        self.assertIs(self.session.state, ScanState.WAITING_BARCODE1)

    def test_reset_also_discards_first_scan(self):
        self.session.consume("old", self.settings)
        self.session.reset()
        self.session.consume("new", self.settings)
        self.assertEqual(self.session.barcode1, "new")

    def test_settings_are_read_at_second_scan(self):
        self.session.consume("123", self.settings)
        self.settings.tolerance_contains = False
        self.settings.tolerance_extra_zero = False
        self.assertFalse(self.session.consume("X123Y", self.settings).match)

    def test_cr_lf_terminates_buffer_once(self):
        for raw in ("ABC\rrest", "ABC\nrest", "ABC\r\nrest"):
            self.assertEqual(normalize_scan(raw), "ABC")


if __name__ == "__main__":
    unittest.main()
