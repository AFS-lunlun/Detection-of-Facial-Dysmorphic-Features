"""Conservative local release check; does not certify that files are anonymous."""
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ALLOWED_ROOT={'README.md','README.zh-CN.md','LICENSE','requirements.txt','pyproject.toml',
              'analysis.py','.gitignore','.gitattributes','TESTING.md'}
PUBLIC_DIRS={'facial_analysis','tests','tools','docs','.github','examples'}
PATTERNS=[re.compile(r'/(?:Users|home)/[^/\s]+/'),
          re.compile(r'[A-Za-z]:\\(?:Users|Documents and Settings)\\'),
          re.compile(r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----'),
          re.compile(r'gh[pousr]_[A-Za-z0-9]{20,}'),
          re.compile(r'(?<![A-Za-z0-9])[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}',re.I)]
IGNORE={'.git','.venv','venv','__pycache__','.pytest_cache'}
fail=[]
for p in ROOT.rglob('*'):
    rel=p.relative_to(ROOT)
    if any(part in IGNORE for part in rel.parts) or not p.is_file():
        continue
    if rel.parts[0] not in PUBLIC_DIRS and str(rel) not in ALLOWED_ROOT:
        fail.append((str(rel),'unexpected item in release directory'));continue
    if p.suffix=='.csv' and str(rel) not in {'examples/synthetic_manifest.csv','examples/synthetic_predictions.csv'}:
        fail.append((str(rel),'non-example CSV'));continue
    if p.suffix.lower() in {'.png','.jpg','.jpeg','.tiff','.pdf','.docx','.pth','.pt','.xlsx','.zip','.json'}:
        fail.append((str(rel),'private or binary artifact type'));continue
    try:
        text=p.read_text(encoding='utf-8')
    except UnicodeError:
        fail.append((str(rel),'non-text file'));continue
    if any(pat.search(text) for pat in PATTERNS):
        fail.append((str(rel),'possible private path, credential, or contact detail'))
if fail:
    for filename,reason in fail:print(filename+': '+reason)
    raise SystemExit(1)
print('Public-file scan passed. Manual review of staged files is still required.')
