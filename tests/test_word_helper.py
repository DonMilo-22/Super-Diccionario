import os
import tempfile
import unittest

import dictionary
import settings
import stats
import used_words
from ocr import correction_candidates, normalize_ocr_text


class WordHelperTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

        self.old_used_folder = used_words.APP_FOLDER
        self.old_used_file = used_words.FILE
        self.old_settings_file = settings.FILE
        self.old_stats_file = stats.FILE

        used_words.APP_FOLDER = self.temp_dir.name
        used_words.FILE = os.path.join(self.temp_dir.name, "used_words.json")
        settings.FILE = os.path.join(self.temp_dir.name, "settings.json")
        stats.FILE = os.path.join(self.temp_dir.name, "stats.json")

    def tearDown(self):
        used_words.APP_FOLDER = self.old_used_folder
        used_words.FILE = self.old_used_file
        settings.FILE = self.old_settings_file
        stats.FILE = self.old_stats_file
        self.temp_dir.cleanup()

    def test_ocr_normalization_and_correction(self):
        self.assertEqual(normalize_ocr_text(" l0-ve!\nly "), "L0VELY")
        self.assertIn("LOVELY", correction_candidates("l0-ve! ly"))

    def test_used_words_filter_both_modes(self):
        used_words.add_used("lovely")
        self.assertNotIn("lovely", [w.lower() for w in dictionary.generate_suggestions("lov", ["love", "lovely"])])
        self.assertNotIn("lovely", [w.lower() for w in dictionary.ends_with("ly", ["lovely", "quickly"])])

    def test_restore_single_used_word(self):
        used_words.add_used("lovely")
        used_words.add_used("lover")
        used_words.remove_used("lovely")
        self.assertNotIn("lovely", used_words.load_used())
        self.assertIn("lover", used_words.load_used())

    def test_profiles_apply_expected_defaults(self):
        current = settings.load_settings()
        updated = settings.apply_profile(current, "Roblox")
        self.assertEqual(updated["language"], "english")
        self.assertTrue(updated["auto_enter"])

    def test_stats_record_and_favorite(self):
        stats.start_session()
        stats.record_word("lovely")
        stats.record_word("lovely")
        self.assertEqual(stats.load_stats()["words"]["lovely"], 2)
        self.assertTrue(stats.toggle_favorite("lovely"))
        self.assertIn("lovely", stats.favorites())

    def test_common_words_rank_first(self):
        results = dictionary.generate_suggestions(
            "lov",
            ["lovecraftian", "lovely", "lover", "love"],
            common_first=True,
        )
        self.assertEqual(results[0].lower(), "love")

    def test_auto_search_checks_start_and_end(self):
        results = dictionary.auto_suggestions(
            "ly",
            ["lyric", "quickly", "slowly"],
            common_first=True,
        )
        lowered = [word.lower() for word in results]
        self.assertIn("lyric", lowered)
        self.assertIn("quickly", lowered)


if __name__ == "__main__":
    unittest.main()
