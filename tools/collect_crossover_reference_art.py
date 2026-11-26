"""Collect explicitly reviewed Wiki references; never mark them as snapshot assets."""
import concurrent.futures,hashlib,io,json,re,urllib.request
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'research/crossover-audit'
def read(name):return json.loads((OUT/name).read_text(encoding='utf8'))
def original(url):return re.sub(r'/scale-to-width-down/\d+(?=\?|$)','',url)
def main():
 icons=read('wiki-icons.json');full=read('wiki-full-images.json')
 sources=[]
 for item in icons:
  if 'Promised Neverland' in item['alt']:continue # Existing snapshot art wins.
  matching=[x for x in full if x['src'].split('/revision/')[0]==item['src'].split('/revision/')[0]]
  if not matching:raise ValueError('Original icon URL not observed: '+item['alt'])
  sources.append(dict(role='icon',label=item['alt'],src=matching[0]['src'],filePage=item['filePage'],context='https://id5.fandom.com/wiki/Essences#Crossover_Essences'))
 candidates=read('wiki-poster-candidates.json')
 wanted={'Persona 5 Crossover':['P5AwakenedPoster.jpg','Persona5Crossover2Poster.jpg'],
 'Death Note Crossover':['DNCrossoverPoster2.jpg'],
 'Case Closed Crossover Part I':['Case_Closed_Poster_P1.png'],
 'Case Closed Crossover Part II':['ConanPart2Poster.jpg'],
 'Bungo Stray Dogs Crossover Part II':['BSD2EssencePoster.jpg'],
 'Angels of Death Crossover':['AngelsOfDeathCrossoverEventPoster.jpeg']}
 for page in candidates:
  for key in wanted.get(page['name'],[]):
   item=next(x for x in page['images'] if x['key']==key)
   sources.append(dict(role='banner',label=key,src=original(item['src']),filePage=item['filePage'],context=page['url'],caption=item['alt'],kind='reference-poster'))
 for page in read('wiki-danganronpa12.json'):
  key='DanganronpaCrossoverInGamePoster.png' if page['part']=='1' else 'DanganronpaPart2InGamePoster.png'
  item=next(x for x in page['images'] if x['key']==key)
  sources.append(dict(role='banner',label=key,src=original(item['src']),filePage=item['filePage'],context=page['url'],caption=item['alt'],kind='reference-ingame-poster'))
 key='DanganronpaPart3CrossoverEssenceInGamePoster.png'
 item=next(x for x in read('wiki-danganronpa3.json') if x['key']==key)
 sources.append(dict(role='banner',label=key,src=original(item['src']),filePage=item['filePage'],context='https://id5.fandom.com/wiki/Danganronpa_Crossover_Part_III',caption=item['alt'],kind='reference-ingame-poster'))
 item=read('wiki-posters.json')[0];sources.append(dict(role='banner',label='XxxHOLiCEssencePoster.jpg',**item))
 dest=ROOT/'public/crossover-art';dest.mkdir(exist_ok=True)
 def fetch(s):
  req=urllib.request.Request(s['src'],headers={'User-Agent':'EssenceLab research asset collector/1.0','Referer':s['context']})
  with urllib.request.urlopen(req,timeout=30) as response:
   raw=response.read(16*1024*1024+1);ctype=response.headers.get('Content-Type');final=response.url
  if len(raw)>16*1024*1024:raise ValueError('16 MiB file budget')
  im=Image.open(io.BytesIO(raw))
  if im.width*im.height>24_000_000:raise ValueError('24 MP budget')
  im.load();digest=hashlib.sha256(raw).hexdigest();ext={'PNG':'.png','JPEG':'.jpg','WEBP':'.webp'}[im.format]
  path=dest/(digest+ext);path.write_bytes(raw)
  return dict(**s,url='/crossover-art/'+path.name,sha256=digest,bytes=len(raw),width=im.width,height=im.height,contentType=ctype,finalUrl=final,origin='wiki-reference',nativeAliasProven=False)
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(fetch,sources))
 (OUT/'reference-art.json').write_text(json.dumps(dict(observed='2026-11-25',policy='Original downloaded bytes, external Wiki references; not recovered game snapshot assets. CDN thumbnail size segment removed for poster originals.',assets=results),indent=2,ensure_ascii=False),encoding='utf8')
 print(json.dumps([dict(label=r['label'],size=[r['width'],r['height']],bytes=r['bytes']) for r in results],ensure_ascii=True))
if __name__=='__main__':main()
