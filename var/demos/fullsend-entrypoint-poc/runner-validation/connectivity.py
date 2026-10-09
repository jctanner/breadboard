"""Read-only service probes; no credentials or response bodies in artifacts."""
import json
import os
import ssl
import sys
import time
import urllib.request
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'scripts'))
import jira_utils
report={'tls_required':jira_utils.ssl_ctx.verify_mode==ssl.CERT_REQUIRED,'hostname_check':jira_utils.ssl_ctx.check_hostname}
try:
    identity=jira_utils.api_call(os.environ['JIRA_SERVER'],'/myself',os.environ['JIRA_USER'],os.environ['JIRA_TOKEN'])
    report['jira_identity_matches']= (identity.get('name') or identity.get('accountId'))==os.environ['JIRA_USER']
except Exception as error:
    report['jira_error']=type(error).__name__
for name,url in {'gitlab':'https://gitlab.local/api/v4/version','orgpulse':'https://orgpulse.local/','github':'https://api.github.com/zen'}.items():
    try:
        request=urllib.request.Request(url,headers={'PRIVATE-TOKEN':os.environ['RESULTS_PUSH_TOKEN']} if name=='gitlab' else {})
        with urllib.request.urlopen(request,timeout=12,context=jira_utils.ssl_ctx) as response:
            report[name]={'status':response.status,'reachable':True}
    except Exception as error:
        report[name]={'reachable':False,'error':str(error)}
for name in ('gitlab','orgpulse'):
    try:
        context=ssl.create_default_context(cafile='/etc/ssl/certs/ca-certificates.crt')
        urllib.request.urlopen('https://'+ ('gitlab.local' if name=='gitlab' else 'orgpulse.local')+'/',timeout=12,context=context)
        report[name+'_wrong_ca_rejected']=False
    except Exception as error:
        report[name+'_wrong_ca_rejected']='CERTIFICATE_VERIFY_FAILED' in str(error)
out=Path(os.environ['FULLSEND_OUTPUT_DIR']);out.mkdir(parents=True,exist_ok=True)
(out/'connectivity.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
hold=int(os.environ.get('M6_HOLD_SECONDS') or '0')
if hold:
    print('M6_LIFECYCLE_READY',file=sys.stderr,flush=True)
    time.sleep(hold)
assert report['gitlab_wrong_ca_rejected'] and report['orgpulse_wrong_ca_rejected']
assert report.get('jira_identity_matches') and all(report[k]['reachable'] for k in ('gitlab','orgpulse','github')), 'M6 connectivity gate failed'
