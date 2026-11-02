import tempfile
from pathlib import Path
import unittest
from file_guard import FileGuard

class FileGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.root=Path(self.tmp.name);self.guard=FileGuard(self.root)
        self.input=self.root/'example.txt';self.input.write_text('Harmless sample')
        self.item=self.guard.upload(self.input)
    def tearDown(self):self.guard.close();self.tmp.cleanup()
    def test_upload_stays_pending(self):
        self.assertEqual(self.item['state'],'PENDING')
        self.assertEqual(list((self.root/'approved').iterdir()),[])
    def test_release_and_duplicate(self):
        event=self.guard.event(self.item['version'])
        for _ in range(2):self.assertEqual(self.guard.process_simulated_event(event)['decision'],'APPROVED')
        self.assertEqual(len(list((self.root/'approved').iterdir())),1)
    def test_all_nonclean_results_block(self):
        for result in ['THREATS_FOUND','UNSUPPORTED','FAILED','ACCESS_DENIED','UNKNOWN']:
            item=self.guard.upload(self.input)
            outcome=self.guard.process_simulated_event(self.guard.event(item['version'],result))
            self.assertEqual(outcome['decision'],'QUARANTINED')
    def test_failed_scan_cannot_release(self):
        e=self.guard.event(self.item['version'],status='FAILED')
        self.assertEqual(self.guard.process_simulated_event(e)['decision'],'QUARANTINED')
    def test_version_mismatch_rejected(self):
        e=self.guard.event(self.item['version']);e['detail']['s3ObjectDetails']['versionId']='different'
        with self.assertRaises(ValueError):self.guard.process_simulated_event(e)
    def test_etag_mismatch_rejected(self):
        e=self.guard.event(self.item['version']);e['detail']['s3ObjectDetails']['eTag']='different'
        with self.assertRaises(ValueError):self.guard.process_simulated_event(e)
    def test_tampered_file_blocked(self):
        (self.root/'quarantine'/self.item['version']).write_text('Changed')
        self.assertEqual(self.guard.process_simulated_event(self.guard.event(self.item['version']))['decision'],'QUARANTINED')
    def test_fake_pdf_blocked(self):
        p=self.root/'fake.pdf';p.write_text('Not a PDF');item=self.guard.upload(p)
        self.assertEqual(self.guard.process_simulated_event(self.guard.event(item['version']))['decision'],'QUARANTINED')
    def test_later_threat_revokes_and_cannot_reapprove(self):
        version=self.item['version']
        self.guard.process_simulated_event(self.guard.event(version))
        self.guard.process_simulated_event(self.guard.event(version,'THREATS_FOUND'))
        self.assertFalse((self.root/'approved'/version).exists())
        self.assertEqual(self.guard.process_simulated_event(self.guard.event(version))['decision'],'QUARANTINED')
    def test_spoofed_envelope_rejected(self):
        e=self.guard.event(self.item['version']);e['source']='other'
        with self.assertRaises(ValueError):self.guard.process_simulated_event(e)
