import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from agent import cached, investigate

class AgentTests(unittest.TestCase):
    def test_cache_reuse_and_expiry(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            self.assertEqual(cached(p,'a',lambda:1),(1,False))
            self.assertEqual(cached(p,'a',lambda:2),(1,True))
            self.assertEqual(cached(p,'a',lambda:3,ttl=-1),(3,False))
    def test_diagnoses_and_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            for scenario in ['database','memory','unknown']:
                report,path=investigate(scenario,base=Path(d))
                self.assertEqual(report['hypothesis'],scenario)
                self.assertTrue((path/'report.html').exists())
                self.assertTrue(json.loads((path/'report.json').read_text())['simulation'])
    def test_failure_preserves_report(self):
        with tempfile.TemporaryDirectory() as d:
            report,_=investigate(simulate_failure=True,base=Path(d))
            self.assertEqual(report['mode'],'rules fallback')
            self.assertEqual(report['trace'][-1]['error_type'],'TimeoutError')
    def test_llm_success(self):
        with tempfile.TemporaryDirectory() as d, patch('agent.model_summary',return_value='Evidence suggests a connection issue.'):
            report,_=investigate(model='test',base=Path(d))
            self.assertEqual(report['mode'],'LLM-assisted analysis')

if __name__=='__main__': unittest.main()
