"""Exercise identities, alias resolution and evidence-scoped set-credit regressions."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / 'packages/python')]
from src.convert_fedb_to_fedbpp import annotate, convert, load_curated_manifest
from fedbpp import Database

DOCUMENT = json.loads((ROOT / 'free-exercise-db-plusplus.json').read_text())
REVIEW = json.loads((ROOT / 'src/specialized_muscle_review.json').read_text())
ADDITIONS = [e for e in load_curated_manifest() if e.get('sourceRefs')]


class SpecializedMuscleTests(unittest.TestCase):
    def test_all_candidates_are_distinct_eligible_movements(self):
        self.assertEqual(len(ADDITIONS), 11)
        expected = {'tibialis': 4, 'hip_flexors': 3, 'neck': 1, 'rotator_cuff': 3}
        for group, count in expected.items():
            entries = [e for e in ADDITIONS if group in e['direct']]
            self.assertEqual(len(entries), count)
            for entry in entries:
                record = DOCUMENT['exercises'][entry['id']]
                self.assertTrue(record['annotation']['volumeEligible'])
                self.assertIn(group, record['annotation']['direct'])
                self.assertGreaterEqual(len(record['source']['instructions']), 3)

    def test_aliases_resolve_without_duplicate_ids_or_changed_upstream_sources(self):
        database = Database(DOCUMENT)
        originals = json.loads((ROOT / 'exercises.json').read_text())
        for original in originals:
            self.assertEqual(DOCUMENT['exercises'][original['id']]['source'], original)
        for eid, aliases in REVIEW['upstreamAliases'].items():
            for alias in aliases:
                matches = database.find_exercises(alias, locale='en')
                self.assertIn(eid, [e.exercise_id for e in matches])
                self.assertNotIn(alias.replace(' ', '_'), DOCUMENT['exercises'])
        self.assertEqual(DOCUMENT['exercises']['External_Rotation']['localizedNames']['en']['preferred'],
                         'Side-Lying Dumbbell External Rotation')

    def test_partial_credit_is_limited_to_reviewed_records(self):
        for eid, annotation in REVIEW['annotationOverrides'].items():
            actual = DOCUMENT['exercises'][eid]['annotation']
            self.assertEqual(actual['indirect'], annotation['indirect'])
            self.assertEqual(actual['confidence'], 'medium')
            for group in ['hip_flexors', 'rotator_cuff']:
                if group in actual['indirect']:
                    self.assertEqual(DOCUMENT['metadata']['setCredits']['indirect'], 0.5)
        for eid in ['Crunches', 'Barbell_Full_Squat', 'Barbell_Shrug', 'Janda_Sit-Up']:
            roles = DOCUMENT['exercises'][eid]['annotation']
            self.assertFalse(set(roles['indirect']) & {'hip_flexors','rotator_cuff','neck','tibialis'})
        self.assertFalse(DOCUMENT['exercises']['Cable_Alternating_Jackknife']['annotation']['volumeEligible'])

    def test_non_volume_category_cannot_be_overridden_into_credit(self):
        source = copy.deepcopy(DOCUMENT['exercises']['Sit-Up']['source'])
        source['category'] = 'stretching'
        annotation = annotate(source)
        self.assertFalse(annotation['volumeEligible'])
        self.assertEqual(annotation['direct'] + annotation['indirect'], [])

    def test_new_exercises_have_all_supported_translations_without_claiming_native_review(self):
        for entry in ADDITIONS:
            names = DOCUMENT['exercises'][entry['id']]['localizedNames']
            for locale in DOCUMENT['metadata']['localization']['supportedLocales']:
                self.assertIn(locale, names)
                self.assertTrue(names[locale]['preferred'].strip())
                if locale != 'en':
                    self.assertEqual(names[locale]['reviewStatus'], 'provisional')

    def test_every_source_has_reason_and_used_sources_resolve_through_patterns(self):
        references = DOCUMENT['metadata']['evidence']['references']
        patterns = DOCUMENT['metadata']['evidence']['patterns']
        for ref_id, reference in REVIEW['references'].items():
            self.assertTrue(reference['reason'])
            self.assertEqual(references[ref_id], reference)
        for entry in ADDITIONS:
            reachable = {ref for p in entry['patterns'] for ref in patterns[p]['references']}
            self.assertLessEqual(set(entry['sourceRefs']), reachable)
        for eid in REVIEW['annotationOverrides']:
            for ref in DOCUMENT['exercises'][eid]['annotation']['evidenceRefs']:
                pattern = patterns[ref.removeprefix('pattern:')]
                self.assertIn('fractional_sets_meta_regression_2025', pattern['references'])


if __name__ == '__main__':
    unittest.main()
