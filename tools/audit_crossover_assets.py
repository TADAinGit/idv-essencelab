"""Bounded atlas/CSB discovery for missing crossover art; game data is never run."""
import json,re,time
from pathlib import Path
from extract_gacha_ui import ROOT,CFG,EssenceResourceStore,sha,write_json

def main():
 out=ROOT/'research/crossover-audit';out.mkdir(exist_ok=True)
 store=EssenceResourceStore(Path(CFG['analysis'])/'resources.sqlite',CFG['game'],out/'payloads')
 prior=json.loads((ROOT/'research/image-audit/report.json').read_text(encoding='utf8'))
 missing={Path(x['requested']).stem:x for x in prior['missingIcons']}
 terms=['p5','persona','danwan','conan','kenan','death_note','bsd','angels_of_death','xxxholic','kid_s']
 atlas=[r[0] for r in store.db.execute("select distinct path from resources where group_name='ui' and (path like '%.plist' or path like '%.atlas')")]
 csb=[r[0] for r in store.db.execute("select distinct path from resources where path like 'ui/%.csb' and (path like '%treasure%' or path like '%p5%' or path like '%xxxholic%' or path like '%danwan%' or path like '%kenan%')")]
 # Atlas frame-name discovery is bounded; no unrelated texture exports.
 paths=sorted(set(atlas+csb));results=[];total=0
 for i,path in enumerate(paths):
  row=store.lookup(path)
  if row['length']>8*1024*1024 or total+row['length']>512*1024*1024:
   results.append(dict(uri=path,status='skipped-budget'));continue
  try:
   raw,stamp=store.read(path);total+=row['length']
   strings=[s.decode('ascii') for s in re.findall(rb'[A-Za-z0-9_./\\-]{4,250}',raw)]
   hits=sorted({s for s in strings if Path(s.replace('\\','/')).stem.lower() in missing})
   related=sorted({s for s in strings if any(t in s.lower() for t in terms)})
   refs=sorted({s for s in strings if re.search(r'\.(?:png|dds|plist|atlas|csb|skel|json)$',s,re.I)})
   results.append(dict(uri=path,status='read',bytes=len(raw),provenance=stamp,missingNameHits=hits,related=related,references=refs))
  except Exception as exc:results.append(dict(uri=path,status='failed',error=str(exc)))
  if (i+1)%100==0:print(f'{i+1}/{len(paths)}',flush=True)
 write_json(out/'atlas-scene-audit.json',dict(snapshot=prior['snapshot'],toolSha256=sha(Path(__file__).read_bytes()),limits=dict(packedPerFile=8*1024*1024,packedTotal=512*1024*1024),packedBytes=total,atlasCount=len(atlas),csbCount=len(csb),results=results))
 store.close();print(json.dumps(dict(scanned=len(results),hits=sum(bool(r.get('missingNameHits')) for r in results),failed=sum(r['status']=='failed' for r in results))))
if __name__=='__main__':main()
