"""Bounded data-only gacha screen asset audit, archive reads remain immutable."""
import json,sys,hashlib,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'config.local.json').read_text(encoding='utf-8'))
sys.path.insert(0,str(Path(CFG['research_project'])/'tools'))
from essence_resource_store import EssenceResourceStore
from extract_gacha_ui import image_decode
OUT=ROOT/'research/game-screen'
PUBLIC=ROOT/'public/game-scene'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);PUBLIC.mkdir(parents=True,exist_ok=True)
 store=EssenceResourceStore(Path(CFG['analysis'])/'resources.sqlite',CFG['game'],OUT/'payloads')
 # Copy index into memory to avoid repeated SQLite scans over the source index.
 import sqlite3
 db=sqlite3.connect(':memory:');store.db.backup(db);store.db.close();store.db=db;db.row_factory=sqlite3.Row
 prefix='ui/dm65ui/res/spine/treasure_list/'
 paths=[r[0] for r in db.execute('SELECT path FROM resources WHERE path LIKE ?',(prefix+'%',))]
 paths+=['ui/dm65ui/res/treasure_list_content.csb']
 # Standard paired atlas names are candidates; verify against indexed identity.
 paths+= [p[:-5]+'.atlas' for p in paths if p.endswith('.skel')]
 records=[]
 for uri in sorted(set(paths)):
  if len(records)>80 or store.bytes_read>64*1024*1024:raise ValueError('Audit budget')
  try:
   raw,provenance=store.read(uri);name=Path(uri).name;dst=PUBLIC/name;dst.write_bytes(raw)
   record=dict(uri=uri,url='/game-scene/'+name,sha256=sha(raw),provenance=provenance)
   if uri.endswith('.dds'):
    img=image_decode(raw);dst=PUBLIC/(Path(uri).stem+'.png');img.save(dst)
    record.update(image='/game-scene/'+dst.name,imageSha256=sha(dst.read_bytes()),size=list(img.size))
   if uri.endswith('.atlas'):record['text']=raw.decode('utf-8')
   records.append(record)
  except (OSError,ValueError) as e:records.append(dict(uri=uri,error=str(e)))
 store.close()
 (OUT/'assets.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps([{k:v for k,v in r.items() if k in ['uri','size','error']} for r in records],indent=2))
if __name__=='__main__':main()
