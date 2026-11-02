"""Read-only CloudWatch CLI adapter and reproducible dummy log replay."""
import argparse
import html
import json
from pathlib import Path
import subprocess
import time
from agent import ROOT, investigate

CASES = {
 'database': ('database', ['INFO deployment completed', 'ERROR database: too many connections', 'ERROR checkout connection timeout']),
 'memory': ('memory', ['INFO deployment completed', 'ERROR container terminated: OOMKilled', 'WARN restart count increased']),
 'ambiguous_timeout': ('unknown', ['ERROR upstream connection timeout', 'WARN high request latency']),
 'conflicting_signals': ('unknown', ['ERROR database: too many connections', 'ERROR container OOMKilled']),
 'empty_logs': ('unknown', []),
}

def normalize(response, service, source):
    events=response.get('events', [])
    if not isinstance(events,list): raise ValueError('events must be a list')
    for e in events:
        if not isinstance(e,dict) or not isinstance(e.get('message'),str):
            raise ValueError('Each event requires a string message')
    return {'service':service,'source':source,'alert':'Log-based investigation','metrics':{},'logs':[e['message'] for e in sorted(events,key=lambda e:e.get('timestamp',0))], 'event_count':len(events), 'coverage':'Bounded log sample; metrics not collected', 'possibly_truncated':bool(response.get('NextToken') or response.get('nextToken'))}

def fetch(group,region,profile=None,minutes=15):
    if not 1 <= minutes <= 1440: raise ValueError('minutes must be 1-1440')
    end=int(time.time()*1000)
    cmd=['aws','logs','filter-log-events','--log-group-name',group,'--region',region,'--start-time',str(end-minutes*60000),'--end-time',str(end),'--max-items','500','--output','json','--no-cli-pager','--cli-connect-timeout','10','--cli-read-timeout','20']
    if profile:cmd+=['--profile',profile]
    result=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
    if result.returncode: raise RuntimeError('CloudWatch read failed. Check AWS login, region, log group and logs:FilterLogEvents permission. No dummy data substituted.')
    return json.loads(result.stdout)

def demo():
    fixtures=ROOT/'fixtures';fixtures.mkdir(exist_ok=True)
    rows=[]
    results=[]
    for name,(expected,messages) in CASES.items():
        response={'events':[{'eventId':f'{name}-{i}','logStreamName':'dummy/app','timestamp':1793620800000+i*1000,'message':m} for i,m in enumerate(messages)]}
        file=fixtures/(name+'.json');file.write_text(json.dumps(response,indent=2))
        evidence=normalize(json.loads(file.read_text()),name,'local synthetic CloudWatch-format fixture')
        report,path=investigate(evidence_override=evidence,simulate_failure=name=='database')
        ok=report['hypothesis']==expected
        results.append({'case':name,'expected':expected,'actual':report['hypothesis'],'passed':ok,'mode':report['mode']})
        rows.append(f'<tr><td>{html.escape(name)}</td><td>{expected}</td><td>{report["hypothesis"]}</td><td>{"PASS" if ok else "FAIL"}</td><td><a href="{path.relative_to(ROOT).as_posix()}/report.html">Open report</a></td></tr>')
    (ROOT/'demo-results.json').write_text(json.dumps(results,indent=2))
    (ROOT/'demo-results.html').write_text('<!doctype html><meta charset="utf-8"><title>Incident replay results</title><style>body{font:16px/1.6 system-ui;max-width:1000px;margin:50px auto;color:#173b4d}td,th{padding:16px;text-align:left;border-bottom:1px solid #ccd}table{border-collapse:collapse;width:100%}</style><h1>CloudWatch-format incident replay</h1><p>LOCAL SIMULATION: synthetic logs; no live AWS calls or live model inference.</p><table><tr><th>Case</th><th>Expected</th><th>Result</th><th>Check</th><th>Evidence</th></tr>'+''.join(rows)+'</table><p>Database case also simulates a model timeout to exercise fallback. Diagnoses are hypotheses, not confirmed root causes.</p>',encoding='utf-8')
    print(json.dumps(results,indent=2))
    if not all(r['passed'] for r in results):raise SystemExit(1)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--live',action='store_true');p.add_argument('--log-group');p.add_argument('--region');p.add_argument('--profile');p.add_argument('--minutes',type=int,default=15);p.add_argument('--model')
    a=p.parse_args()
    if a.live:
        if not a.log_group or not a.region:p.error('--live needs --log-group and --region')
        evidence=normalize(fetch(a.log_group,a.region,a.profile,a.minutes),a.log_group,'AWS CloudWatch Logs via read-only CLI')
        report,path=investigate(evidence_override=evidence,simulation=False,model=a.model)
        print(report['summary']);print(path/'report.html')
    else:demo()
