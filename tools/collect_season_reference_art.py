"""Select Wiki artwork by season/Essence section, preserving source provenance."""
import concurrent.futures,hashlib,io,json,re,urllib.request
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/season-posters'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def identity(box):
 # Localized Global title outranks the release season of historical reruns.
 m=re.match(r'^(?:S|Season\s+)(\d+)\b.*?Essence\s*(\d+)\b',box['name'])
 if m:return tuple(map(int,m.groups()))
 pair=box['configuration'].get('show_img_num')
 return tuple(pair) if pair and len(pair)==2 else None
def family(box):return bool(re.search(r'Crossover|GACHINAME|KENAN|WENHAO|XXXHOLIC|SHENGDIAN_TREASURE|Abyss Treasure',box['name']+' '+box['nameTid'],re.I))
def score(item,s,e):
 text=item['key']+' '+item['alt']
 # Wiki's "InGameBanner" is often an 800x140 announcement strip, not a backdrop.
 if re.search(r'In.?Game.?Banner',text,re.I):return 5
 if re.search(r'In.?Game.?Poster',text,re.I):return 90
 points=40 if re.search(r'(?:S'+str(s)+r'.?E'+str(e)+r'|Season.?'+str(s)+r'.?Essence.?'+str(e)+r')',text,re.I) else 20
 if 'New' in item['key']:points+=10
 if any(x in item['key'] for x in ['Old','KR','PhoneWallpaper','EventPoster','Announcement']):points-=15
 return points
def main():
 cat=read(ROOT/'public/data/catalog.json');selected=[];missing=[]
 previous=read(OUT/'reference-art.json').get('records',{}) if (OUT/'reference-art.json').exists() else {}
 cached={r['originalUrl']:r for r in previous.values()}
 for box in cat['boxes']:
  if box['category']!='season' or family(box):continue
  pair=identity(box)
  if not pair or not 1<=pair[0]<=39:continue
  s,e=pair
  # Bloodbath was labeled E2 in client, but is the third Logic Path essence.
  wiki_e=3 if box['id']=='75' else e
  page=read(OUT/f'season-{s}.json')
  candidates=[i for i in page['images'] if re.search(r'Essence\s*'+str(wiki_e)+r'\b',i['section'],re.I) and i.get('src','').startswith('https://static.wikia.nocookie.net/id5/')]
  if not candidates:missing.append(dict(id=box['id'],name=box['name'],season=s,essence=e,reason='No matching Essence artwork in reviewed Wiki season section'));continue
  art=max(candidates,key=lambda i:score(i,s,wiki_e))
  src=art['filePage'] if art.get('filePage','').startswith('https://static.wikia.nocookie.net/id5/') else re.sub(r'/scale-to-width-down/\d+(?=\?|$)','',art['src'])
  selected.append(dict(boxId=box['id'],name=box['name'],season=s,essence=e,wikiEssence=wiki_e,context=page['url'],originalUrl=src,**art))
 dest=ROOT/'public/season-art';dest.mkdir(exist_ok=True)
 unique={r['originalUrl']:r for r in selected}
 def fetch(pair):
  url,r=pair;req=urllib.request.Request(url,headers={'User-Agent':'EssenceLab artwork collector/1.0','Referer':r['context']})
  old=cached.get(url)
  if old and hashlib.sha256((ROOT/('public'+old['url'])).read_bytes()).hexdigest()==old['sha256']:
   return url,{k:old[k] for k in ['url','downloadUrl','sha256','width','height','bytes','origin','nativeAliasProven'] if k in old}
  with urllib.request.urlopen(req,timeout=35) as response:raw=response.read(16*1024*1024+1)
  if len(raw)>16*1024*1024:raise ValueError('16MiB file bound')
  im=Image.open(io.BytesIO(raw));download_url=url
  if im.width*im.height>32_000_000:
   # Request the CDN's proportion-preserving display derivative, retaining both URLs.
   head,sep,query=url.partition('?');download_url=head+'/scale-to-width-down/2560'+(sep+query if sep else '')
   with urllib.request.urlopen(urllib.request.Request(download_url,headers={'User-Agent':'EssenceLab artwork collector/1.0'}),timeout=35) as response:raw=response.read(16*1024*1024+1)
   if len(raw)>16*1024*1024:raise ValueError('16MiB derivative bound')
   im=Image.open(io.BytesIO(raw))
   if im.width*im.height>32_000_000:raise ValueError('32MP derivative bound')
  im.load();digest=hashlib.sha256(raw).hexdigest();ext={'PNG':'.png','JPEG':'.jpg','WEBP':'.webp'}[im.format]
  p=dest/(digest+ext);p.write_bytes(raw)
  return url,dict(url='/season-art/'+p.name,downloadUrl=download_url,sha256=digest,width=im.width,height=im.height,bytes=len(raw),origin='wiki-reference',nativeAliasProven=False)
 downloaded={};errors={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  futures={pool.submit(fetch,pair):pair[0] for pair in unique.items()}
  for future in concurrent.futures.as_completed(futures):
   url=futures[future]
   try:key,val=future.result();downloaded[key]=val
   except Exception as exc:errors[url]=str(exc)
 records={r['boxId']:{**r,**downloaded[r['originalUrl']], 'presentation':'strip' if downloaded[r['originalUrl']]['width']/downloaded[r['originalUrl']]['height']>3.5 else 'poster'} for r in selected if r['originalUrl'] in downloaded}
 report=dict(observed='2026-11-25',records=records,missing=missing,downloadErrors=errors,sourceCatalogSha256=hashlib.sha256((ROOT/'public/data/catalog.json').read_bytes()).hexdigest())
 (OUT/'reference-art.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
 print(json.dumps(dict(mappedRecords=len(records),uniqueImages=len(downloaded),missing=missing,errors=errors),ensure_ascii=True))
if __name__=='__main__':main()
