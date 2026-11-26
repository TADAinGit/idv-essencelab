"""Download exact-section alternative Wiki posters for visual review, never publish by score alone."""
import concurrent.futures, hashlib, io, json, re, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/ui-polish'
def main():
 OUT.mkdir(exist_ok=True); (OUT/'candidates').mkdir(exist_ok=True)
 report=json.loads((ROOT/'research/season-posters/reference-art.json').read_text(encoding='utf8'))
 unique={(r['season'],r['wikiEssence']):r for r in report['records'].values()}
 candidates=[]
 for (s,e),current in sorted(unique.items()):
  page=json.loads((ROOT/f'research/season-posters/season-{s}.json').read_text(encoding='utf8'))
  for item in page['images']:
   if not re.search(r'Essence\s*'+str(e)+r'\b',item['section'],re.I):continue
   if not re.search('Poster',item['key'],re.I) or re.search('In.?Game|Phone|Concept|Design|KR|Old|Announcement',item['key'],re.I):continue
   url=re.sub(r'/scale-to-width-down/\d+(?=\?|$)','',item['src'])
   candidates.append(dict(season=s,essence=e,boxId=current['boxId'],context=page['url'],**item,originalUrl=url))
 def fetch(r):
  path=OUT/'candidates'/r['key']
  if path.exists():raw=path.read_bytes()
  else:
   with urllib.request.urlopen(urllib.request.Request(r['originalUrl'],headers={'User-Agent':'EssenceLab artwork review/1.0'}),timeout=30) as f:raw=f.read(16*1024*1024+1)
  if len(raw)>16*1024*1024:raise ValueError('16MiB bound')
  im=Image.open(io.BytesIO(raw))
  if im.width*im.height>40_000_000:raise ValueError('40MP bound')
  im.load();path.write_bytes(raw)
  return {**r,'file':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'width':im.width,'height':im.height,'bytes':len(raw)}
 rows=[];errors=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  pending={pool.submit(fetch,r):r for r in candidates}
  for f in concurrent.futures.as_completed(pending):
   try:rows.append(f.result())
   except Exception as ex:errors.append(dict(key=pending[f]['key'],error=str(ex)))
 rows.sort(key=lambda r:(r['season'],r['essence'],r['key']))
 (OUT/'art-candidates.json').write_text(json.dumps(dict(records=rows,errors=errors),indent=2,ensure_ascii=False),encoding='utf8')
 for label,items in [('current',list(sorted(unique.values(),key=lambda r:(r['season'],r['essence'])))),('alternatives',rows)]:
  for start in range(0,len(items),18):
   sheet=Image.new('RGB',(1500,6*210),'#25222b');draw=ImageDraw.Draw(sheet)
   for i,r in enumerate(items[start:start+18]):
    path=ROOT/r['file'] if 'file' in r else ROOT/('public'+r['url'])
    im=Image.open(path).convert('RGB');im.thumbnail((490,180));x=(i%3)*500;y=(i//3)*210
    sheet.paste(im,(x+(490-im.width)//2,y));draw.text((x+5,y+181),f"S{r['season']}E{r.get('wikiEssence',r.get('essence'))} #{r['boxId']} {r['key']}",fill='white')
   sheet.save(OUT/f'{label}-{start//18+1}.jpg',quality=90)
 print(json.dumps(dict(candidates=len(rows),errors=errors)))
if __name__=='__main__':main()
