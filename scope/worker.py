"""One frozen original-model diagnosis run; no repair or parameter selection."""
import sys,json,time,resource
from pathlib import Path
from dataclasses import asdict,is_dataclass
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(BASE/'deps'))
cfg=json.loads((ROOT/'freeze.json').read_text())
task=cfg['tasks'][int(sys.argv[1])]
t=time.perf_counter()
row={'task_id':task['id'],'case_id':task['case_id'],'method':task['method'],'family':task['family']}
try:
    if task['family']=='p2':
        p=Path(cfg['p2_root']);sys.path[:0]=[str(p/'src'),str(p/'experiments/scripts')]
        from g2_wiring import load_g2_model
        from lstpn.probability import diagnose_probability,_default_probability_budget
        from lstpn.certificates import CertificateScope
        model=load_g2_model(task['path'])
        cert=diagnose_probability(model,'medium',_default_probability_budget(),scope=CertificateScope.RISK_COVERAGE_ONLY)
        row['certificate']=asdict(cert)
        row['execution_status']='COMPLETED'
        # decision=None explicitly denotes inability to issue a risk certificate.
        row['risk_decision']=cert.decision.value if cert.decision is not None else 'UNKNOWN'
    else:
        sys.path.insert(0,cfg['p1_root'])
        from src.model.parser import parse_model
        from src.verifier import verify
        from src.baselines.mscg_lp_complete import verify_mscg_lp_complete
        from src.baselines.no_sync import verify_no_sync
        from src.baselines.no_envelope import verify_no_envelope
        if task['family']=='micro': net,L,H=parse_model(task['path'])
        else:
            from src.benchmarks.rmt_fms_generator import generate_rmt_fms
            net,L,H=generate_rmt_fms(**task['params'])
        fn={'main':verify,'reference':verify_mscg_lp_complete,'no_sync':verify_no_sync,'no_envelope':verify_no_envelope}[task['method']]
        result=fn(net,L,H)
        row.update(execution_status='COMPLETED',L=L,H=H,n_places=len(net.places),n_transitions=len(net.transitions),result=result)
except Exception as e:
    row.update(execution_status='COMPUTATION_FAILURE',conservative_verdict='UNKNOWN' if task['family']=='p2' else 'INC',error=f'{type(e).__name__}: {e}')
row.update(wall_s=time.perf_counter()-t,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024)
print(json.dumps(row,ensure_ascii=False,default=lambda o:asdict(o) if is_dataclass(o) else getattr(o,'value',str(o))))
