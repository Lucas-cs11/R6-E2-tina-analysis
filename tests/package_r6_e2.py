#!/usr/bin/env python3
"""Create and independently extract-verify the R6-E2 partial evidence archives."""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = {'SHA256SUMS', 'SHA256SUMS.portable', 'R6_E2_complete_workspace.zip',
             'R6_E2_portable_evidence.zip', 'R6_E2_archive_verification.txt'}
PORTABLE_EXCLUDE = ('baseline_readonly/R6_E1_complete_workspace.zip', 'baseline_readonly/R6_E1_portable_evidence.zip')
for name in ARTIFACTS:
    if (ROOT / name).exists(): raise SystemExit('refusing to overwrite ' + name)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()


def collect(portable=False):
    out = []
    for base, dirs, files in os.walk(ROOT):
        for name in files:
            p = Path(base) / name
            rel = p.relative_to(ROOT).as_posix()
            if rel in ARTIFACTS or p.is_symlink(): continue
            if portable and any(rel.startswith(x) for x in PORTABLE_EXCLUDE): continue
            out.append((p, rel))
    return sorted(out, key=lambda x: x[1])


def write_manifest(files, path):
    with path.open('w', encoding='utf-8') as f:
        for p, rel in files: f.write(f'{sha(p)}  {rel}\n')


def make_zip(files, path, manifest=None):
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for p, rel in files: z.write(p, 'R6_E2/' + rel)
        if manifest: z.write(manifest[0], 'R6_E2/' + manifest[1])
    with zipfile.ZipFile(path) as z:
        bad = z.testzip(); names = [PurePosixPath(n).as_posix() for n in z.namelist()]
        if len(names) != len(set(names)): raise SystemExit('duplicate zip member')
        if any(n.startswith('/') or '..' in PurePosixPath(n).parts for n in names): raise SystemExit('unsafe zip path')
        return len(names), bad


def extract_verify(zip_path):
    with tempfile.TemporaryDirectory(prefix='r6e2verify_') as tmp:
        with zipfile.ZipFile(zip_path) as z: z.extractall(tmp)
        root = Path(tmp) / 'R6_E2'
        proc = subprocess.run([sys.executable, 'tests/final_verify_r6_e2.py'], cwd=root, text=True, capture_output=True)
        return {'exit_code': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr}


complete = collect(False); portable = collect(True)
write_manifest(complete, ROOT / 'SHA256SUMS'); write_manifest(portable, ROOT / 'SHA256SUMS.portable')
complete_zip = ROOT / 'R6_E2_complete_workspace.zip'; portable_zip = ROOT / 'R6_E2_portable_evidence.zip'
cm, cbad = make_zip(complete, complete_zip, (ROOT / 'SHA256SUMS', 'SHA256SUMS'))
pm, pbad = make_zip(portable, portable_zip, (ROOT / 'SHA256SUMS.portable', 'SHA256SUMS.portable'))
record = {
    'created_at': datetime.now().astimezone().isoformat(), 'overall_status': 'PARTIAL_VALIDATED_NOT_CLOSED',
    'complete_archive': {'path': complete_zip.name, 'sha256': sha(complete_zip), 'size': complete_zip.stat().st_size, 'members': cm, 'crc_error': cbad},
    'portable_archive': {'path': portable_zip.name, 'sha256': sha(portable_zip), 'size': portable_zip.stat().st_size, 'members': pm, 'crc_error': pbad,
                         'excluded_prefixes': list(PORTABLE_EXCLUDE)},
    'complete_extracted_verifier': extract_verify(complete_zip),
    'portable_extracted_verifier': extract_verify(portable_zip),
}
(ROOT / 'R6_E2_archive_verification.txt').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'complete': record['complete_archive'], 'portable': record['portable_archive'],
                  'complete_verify': record['complete_extracted_verifier']['exit_code'],
                  'portable_verify': record['portable_extracted_verifier']['exit_code']}, indent=2))
raise SystemExit(0 if record['complete_extracted_verifier']['exit_code'] == 0 and record['portable_extracted_verifier']['exit_code'] == 0 else 1)
