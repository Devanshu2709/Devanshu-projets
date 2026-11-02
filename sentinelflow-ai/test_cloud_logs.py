import unittest
from cloud_logs import normalize
from agent import select_hypothesis

class LogTests(unittest.TestCase):
    def test_sort_and_no_fake_metrics(self):
        e=normalize({'events':[{'timestamp':2,'message':'second'},{'timestamp':1,'message':'first'}]},'app','test')
        self.assertEqual(e['logs'],['first','second'])
        self.assertEqual(e['metrics'],{})
    def test_timeout_is_not_proof_of_database_failure(self):
        self.assertEqual(select_hypothesis({'logs':['connection timeout']}),'unknown')
    def test_conflict_escalates(self):
        self.assertEqual(select_hypothesis({'logs':['OOMKilled; too many connections']}),'unknown')
    def test_bad_event_rejected(self):
        with self.assertRaises(ValueError):normalize({'events':[{'message':4}]},'app','test')
    def test_truncation_disclosed(self):
        self.assertTrue(normalize({'events':[],'NextToken':'more'},'app','test')['possibly_truncated'])
