import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from agent import investigate
from rag import retrieve,validate

class RagTests(unittest.TestCase):
    def test_known_incident_excludes_unrelated_runbook(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as d:
            report,_=investigate('database',base=Path(d))
            self.assertNotIn('memory',[x['id'] for x in report['retrieved_documents']])
    def test_retrieval(self):
        self.assertEqual(retrieve('database too many connections pool exhausted')[0]['id'],'database')
        self.assertEqual(retrieve('memory OOMKilled container restarts')[0]['id'],'memory')
        self.assertEqual(retrieve(''),[])
    def test_invalid_citation_rejected(self):
        value={'summary':'test','suggestions':[{'action':'check','rationale':'test','verification':'check','citations':['invented']}]}
        with self.assertRaises(ValueError):validate(value,retrieve('database'))
    def test_uncertainty_overrides_model_mitigation(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as d,patch('agent.generate',return_value={'summary':'Unclear','suggestions':[{'action':'Bad mitigation'}]}):
            report,_=investigate('unknown',model='test',base=Path(d))
            self.assertEqual(report['ai_suggestions'],[])
    def test_mcp_subprocess(self):
        messages=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'test','version':'1'}}},{'jsonrpc':'2.0','method':'notifications/initialized'},{'jsonrpc':'2.0','id':2,'method':'tools/list'},{'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'search_runbooks','arguments':{'query':'OOMKilled memory'}}}]
        result=subprocess.run([sys.executable,str(Path(__file__).parent/'mcp_server.py')],input='\n'.join(json.dumps(m) for m in messages)+'\n',text=True,capture_output=True,timeout=10,check=True)
        replies=[json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(replies),3)
        self.assertEqual(len(replies[1]['result']['tools']),2)
        self.assertEqual(json.loads(replies[2]['result']['content'][0]['text'])[0]['id'],'memory')
