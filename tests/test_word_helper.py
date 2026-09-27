import os
import tempfile
import unittest

import dictionary
import used_words
from main import normalize_ocr_text


class WordHelperTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_folder = used_words.APP_FOLDER
        self.original_file = used_words.FILE

        used_words.APP_FOLDER = self.temp_dir.name
        used_words.FILE = os.path.join(self.temp_dir.name, "used_words.json")

    def tearDown(self):
        used_words.APP_FOLDER = self.original_folder
        used_words.FILE = self.original_file
        self.temp_dir.cleanup()

    def test_normalize_ocr_text_removes_noise(self):
        self.assertEqual(
            normalize_ocr_text("  lo-ve!\nly 123 "),
            "LOVELY",
        )

    def test_used_words_are_filtered_from_start_results(self):
        used_words.add_used("lovely")
        results = dictionary.generate_suggestions(
            "lov",
            ["love", "lovely", "lover"],
        )
        self.assertNotIn("lovely", [word.lower() for word in results])

    def test_used_words_are_filtered_from_end_results(self):
        used_words.add_used("lovely")
        results = dictionary.ends_with(
            "ly",
            ["lovely", "quickly", "slowly"],
        )
        self.assertNotIn("lovely", [word.lower() for word in results])
        self.assertIn("quickly", [word.lower() for word in results])

    def test_suggestion_buckets_do_not_duplicate_words(self):
        results = dictionary.generate_suggestions(
            "a",
            ["an", "able", "about", "amazing", "abcdefghijkl", "abcdefghijklm"],
        )
        lowered = [word.lower() for word in results]
        self.assertEqual(len(lowered), len(set(lowered)))


if __name__ == "__main__":
    unittest.main()
