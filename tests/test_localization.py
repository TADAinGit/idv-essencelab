import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from essence_localization import resolve_tid


class LocalizationTest(unittest.TestCase):
    def setUp(self):
        self.texts = {'TID_FACE_COLORFUL_NAME': "%s's Colorful Memory Portrait",
                      'TID_CIVILIAN_SPY': '"Faro Lady"',
                      'TID_SEASON_T_COLLECTION_1': '%s Essence 1', 'TID_SEASON_45': 'Season 45'}

    def test_observed_templates(self):
        self.assertEqual(resolve_tid('TID_FACE_COLORFUL_NAME(TID_CIVILIAN_SPY)', self.texts),
                         '"Faro Lady"\'s Colorful Memory Portrait')
        self.assertEqual(resolve_tid('TID_SEASON_T_COLLECTION_1(TID_SEASON_45)', self.texts),
                         'Season 45 Essence 1')

    def test_literal_percent_and_trimmed_arguments(self):
        self.assertEqual(resolve_tid('TID_EXAMPLE(  value , )', {'TID_EXAMPLE': '%s / 100%%'}), 'value / 100%')

    def test_unsupported_syntax_is_preserved(self):
        for source in ['TID_FACE_COLORFUL_NAME(a,b)', 'TID_FACE_COLORFUL_NAME(TID_OTHER(a))',
                       'TID_UNKNOWN(a)', '__import__(os)']:
            self.assertEqual(resolve_tid(source, self.texts), source)


if __name__ == '__main__':
    unittest.main()
