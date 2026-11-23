"""Bounded isolated jobs; all rows and failures retained. Source bytes checked."""
from pathlib import Path
import sys,json,hashlib,subprocess,os,time
from concurrent.futures import ThreadPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[1];f=ROOT/'freeze.json';cfg=json.loads(f.read_text())
def integrity():
    for p,h in cfg['source_sha256'].items(): assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
integrity()
environment={**os.environ,'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1','PYTHONDONTWRITEBYTECODE':'1'}
def execute(i):
    task=cfg['tasks'][i];start=time.perf_counter()
    command=[sys.executable,str(ROOT/'code/worker.py'),str(i)]
    try:
        proc=subprocess.run(command,capture_output=True,text=True,timeout=cfg['row_wall_s'],env=environment)
        stdout=proc.stdout;stderr=proc.stderr
        if proc.returncode or not stdout.strip():
            row={'execution_status':'PROCESS_FAILURE','exit_code':proc.returncode}
        else:
            try: row=json.loads(stdout.splitlines()[-1])
            except Exception: row={'execution_status':'OUTPUT_FAILURE'}
    except subprocess.TimeoutExpired as e:
        row={'execution_status':'TIMEOUT','conservative_verdict':'UNKNOWN' if task['family']=='p2' else 'INC'}
        stdout=e.stdout or b'';stderr=e.stderr or b''
        if isinstance(stdout,bytes): stdout=stdout.decode(errors='replace')
        if isinstance(stderr,bytes): stderr=stderr.decode(errors='replace')
    row.update(task_id=task['id'],case_id=task['case_id'],method=task['method'],family=task['family'],process_wall_s=time.perf_counter()-start,command=command)
    (ROOT/'logs'/f'{i:03d}.stdout').write_text(stdout)
    (ROOT/'logs'/f'{i:03d}.stderr').write_text(stderr)
    (ROOT/'results'/f'{i:03d}.json').write_text(json.dumps(row,ensure_ascii=False,indent=2)+'\n')
    return row
rows=[]
with ThreadPoolExecutor(max_workers=cfg['workers']) as executor:
    for n,future in enumerate(as_completed([executor.submit(execute,i) for i in range(len(cfg['tasks']))]),1):
        row=future.result();rows.append(row)
        if n%20==0 or row['family']=='p2': print(n,len(cfg['tasks']),row['case_id'],row['method'],row['execution_status'],flush=True)
rows.sort(key=lambda x:x['task_id'])
(ROOT/'results/runs.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
integrity()
print('SOURCE_BYTES_UNCHANGED',len(rows),flush=True)
