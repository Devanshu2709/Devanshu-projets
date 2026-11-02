"""Local quarantine/release prototype. Scan results are simulated, not antivirus verdicts."""
import argparse
import hashlib
import html
import json
from pathlib import Path
import shutil
import sqlite3
import uuid

ROOT=Path(__file__).resolve().parent
MAX_BYTES=10*1024*1024
BUCKET='demo-quarantine'

class FileGuard:
    def __init__(self,root):
        self.root=Path(root)
        for name in ['quarantine','approved']:(self.root/name).mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(self.root/'audit.sqlite')
        self.db.row_factory=sqlite3.Row
        self.db.execute('CREATE TABLE IF NOT EXISTS objects(version TEXT PRIMARY KEY,name TEXT,etag TEXT,sha256 TEXT,kind TEXT,valid INTEGER,state TEXT,reason TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,version TEXT,result TEXT,decision TEXT,created TEXT DEFAULT CURRENT_TIMESTAMP)')
        self.db.commit()
    def close(self):self.db.close()
    def upload(self,path):
        path=Path(path)
        if path.stat().st_size>MAX_BYTES:raise ValueError('File exceeds 10 MiB limit')
        data=path.read_bytes()
        if len(data)>MAX_BYTES:raise ValueError('File exceeds 10 MiB limit')
        ext=path.suffix.lower();valid=False
        if ext=='.pdf':valid=data.startswith(b'%PDF-')
        elif ext=='.png':valid=data.startswith(b'\x89PNG\r\n\x1a\n')
        elif ext in ['.jpg','.jpeg']:valid=data.startswith(b'\xff\xd8\xff')
        elif ext=='.txt':
            try:data.decode('utf-8');valid=b'\x00' not in data
            except UnicodeDecodeError:pass
        version=uuid.uuid4().hex
        sha=hashlib.sha256(data).hexdigest()
        # Local opaque identity token only; real S3 ETags are not SHA-256 hashes.
        etag=uuid.uuid4().hex
        (self.root/'quarantine'/version).write_bytes(data)
        with self.db:
            self.db.execute('INSERT INTO objects VALUES(?,?,?,?,?,?,?,?)',(version,path.name,etag,sha,ext,int(valid),'PENDING','Awaiting simulated scan result'))
        return dict(self.db.execute('SELECT * FROM objects WHERE version=?',(version,)).fetchone())
    def event(self,version,result='NO_THREATS_FOUND',status='COMPLETED'):
        row=self.db.execute('SELECT * FROM objects WHERE version=?',(version,)).fetchone()
        if not row:raise ValueError('Unknown version')
        return {'source':'aws.guardduty','detail-type':'GuardDuty Malware Protection Object Scan Result','account':'000000000000','region':'ca-central-1','detail':{'schemaVersion':'1.0','resourceType':'S3_OBJECT','scanStatus':status,'s3ObjectDetails':{'bucketName':BUCKET,'objectKey':row['name'],'versionId':version,'eTag':row['etag']},'scanResultDetails':{'scanResultStatus':result}}}
    def process_simulated_event(self,event):
        """Never use as an authenticated AWS ingress endpoint."""
        if event.get('source')!='aws.guardduty' or event.get('detail-type')!='GuardDuty Malware Protection Object Scan Result' or event.get('account')!='000000000000' or event.get('region')!='ca-central-1':raise ValueError('Unexpected simulated event envelope')
        detail=event.get('detail',{});obj=detail.get('s3ObjectDetails',{})
        version=obj.get('versionId')
        if not isinstance(version,str):raise ValueError('Missing object version')
        row=self.db.execute('SELECT * FROM objects WHERE version=?',(version,)).fetchone()
        if not row:raise ValueError('Unknown object version')
        if detail.get('resourceType')!='S3_OBJECT' or obj.get('bucketName')!=BUCKET or obj.get('objectKey')!=row['name'] or obj.get('eTag')!=row['etag']:raise ValueError('Object identity mismatch')
        result=detail.get('scanResultDetails',{}).get('scanResultStatus','MISSING')
        src=self.root/'quarantine'/version;dest=self.root/'approved'/version
        reason='Scan did not complete successfully';decision='QUARANTINED'
        if result=='THREATS_FOUND':reason='Scanner reported a potential threat'
        if row['state']=='QUARANTINED':reason='Previously blocked; manual review required'
        elif not src.exists() or hashlib.sha256(src.read_bytes()).hexdigest()!=row['sha256']:reason='Quarantined content changed or missing'
        elif not row['valid']:reason='File type or encoding validation failed'
        elif detail.get('scanStatus')=='COMPLETED' and result=='NO_THREATS_FOUND':
            decision='APPROVED';reason='Simulated no-threat result and basic validation passed'
        if decision=='APPROVED':
            # Write only the verified byte content; reports/database never execute it.
            data=src.read_bytes()
            if hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('Content changed during release')
            dest.write_bytes(data)
        elif dest.exists():dest.unlink()
        with self.db:
            self.db.execute('UPDATE objects SET state=?,reason=? WHERE version=?',(decision,reason,version))
            self.db.execute('INSERT INTO events(version,result,decision) VALUES(?,?,?)',(version,result,decision))
        return {'version':version,'decision':decision,'reason':reason,'scan_result':result,'simulation':True}

def demo():
    root=ROOT/'file-demo'/uuid.uuid4().hex[:8]
    inputs=root/'inputs';inputs.mkdir(parents=True)
    guard=FileGuard(root);results=[]
    for name,result,status in [('no_threats','NO_THREATS_FOUND','COMPLETED'),('malware_flag','THREATS_FOUND','COMPLETED'),('encrypted_or_unsupported','UNSUPPORTED','SKIPPED'),('scanner_failed','FAILED','FAILED'),('access_denied','ACCESS_DENIED','SKIPPED')]:
        path=inputs/(name+'.txt');path.write_text('Harmless demonstration text. No malware is included.')
        item=guard.upload(path)
        outcome=guard.process_simulated_event(guard.event(item['version'],result,status))
        results.append({'case':name,**outcome})
    guard.close()
    (root/'results.json').write_text(json.dumps(results,indent=2))
    rows=''.join('<tr><td>'+html.escape(r['case'])+'</td><td>'+r['scan_result']+'</td><td>'+r['decision']+'</td></tr>' for r in results)
    report=root/'report.html'
    report.write_text('<!doctype html><meta charset="utf-8"><title>File security workflow</title><style>body{font:16px/1.6 system-ui;max-width:950px;margin:50px auto;color:#19384a}td,th{padding:15px;border-bottom:1px solid #ccc;text-align:left}table{width:100%;border-collapse:collapse}</style><h1>File quarantine and release demo</h1><p>SIMULATION ONLY. No antivirus scanner or AWS service was invoked. All sample files contain harmless text; verdicts are injected fixtures.</p><table><tr><th>Case</th><th>Simulated scan result</th><th>Routing decision</th></tr>'+rows+'</table><p>Only the no-threat case reaches the local approved folder. SQLite stores metadata and audit events. This does not establish that a file is malware-free.</p>',encoding='utf-8')
    print(report)
    print(json.dumps(results,indent=2))

if __name__=='__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    demo()
