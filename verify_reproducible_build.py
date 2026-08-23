import argparse,hashlib,os,subprocess,sys,tempfile
from pathlib import Path
ap=argparse.ArgumentParser(); ap.add_argument("input",type=Path); ap.add_argument("--schema",type=Path,required=True); a=ap.parse_args()
root=Path(__file__).resolve().parent; env=os.environ.copy(); env["SOURCE_DATE_EPOCH"]="0"
def build(p):
    subprocess.run([sys.executable,str(root/"convert_fedb_to_fedbpp.py"),str(a.input),str(p),"--schema",str(a.schema),"--completeness","full"],check=True,env=env)
    return hashlib.sha256(p.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory() as td:
    x=Path(td)/"a.json"; y=Path(td)/"b.json"; hx=build(x); hy=build(y)
    assert hx==hy and x.read_bytes()==y.read_bytes()
    print("reproducible build SHA-256:",hx)
