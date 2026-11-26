"""Apply reviewed clean poster selections and non-destructive presentation crops.

The source image is preserved byte for byte. Viewports omit peripheral branding;
they are browser layout, never claimed to be recovered historical native artwork.
"""
import hashlib,json,shutil
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'research/ui-polish'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def main():
 source=ROOT/'research/season-posters/reference-art.json';backup=OUT/'season-art-before.json'
 if not backup.exists():shutil.copyfile(source,backup)
 report=read(backup);candidates=read(OUT/'art-candidates.json')['records']
 # Exact filenames from the retained Wiki section observations, reviewed visually.
 replacements={
 95:'S9E1Poster.jpg',107:'TeahouseTalesPoster2.jpg',205:'S18E3Poster2.png',248:'S22E2Poster.jpg',
 249:'S22E3Poster.jpg',258:'S23E1Poster.jpg',259:'S24E1Poster.jpg',281:'S25E2Poster.jpg',282:'S25E3Poster.jpg',
 397:'S35E1Poster.jpg',399:'S35E3Poster.jpg',414:'S36E2Poster.jpg',424:'S37E1Poster.jpg',425:'S37E2PosterNew.jpg',
 426:'S37E3Poster.jpg',437:'S38E1Poster.jpg',439:'S38E3Poster.jpg',440:'S39E1Poster.png',441:'S39E2Poster.jpg',442:'S39E3Poster.jpg'}
 crops={
 22:(0,.0,1,.86),23:(0,0,1,.80),24:(0,0,1,.91),32:(0,0,1,1),33:(0,0,1,.85),34:(0,.14,1,1),43:(0,.20,1,1),
 52:(0,.10,1,1),53:(0,0,1,.87),54:(0,0,1,.88),62:(0,.09,1,1),63:(0,0,1,.86),64:(0,0,1,.92),73:(0,0,1,.84),
 75:(0,.10,1,1),83:(0,.10,1,1),84:(0,.10,1,1),95:(0,.10,1,1),97:(0,.10,1,1),105:(0,0,1,.79),106:(0,.10,1,1),107:(0,.10,1,1),
 115:(.32,0,1,.92),117:(0,0,1,.80),134001:(0,.10,1,1),135:(0,.10,1,.94),136:(0,.10,1,.90),147:(0,.13,1,1),148:(0,.10,1,.85),
 159:(0,.10,1,.86),171:(0,.10,1,.85),172:(0,.10,1,1),181:(0,.10,1,.85),183:(0,.22,1,.85),192:(0,0,1,.80),193:(.20,0,1,.94),194:(0,0,1,.85),
 204:(0,.10,1,.96),205:(0,.16,1,.80),214:(0,0,1,.81),216:(0,.13,1,.93),225:(0,0,1,.86),226:(0,.19,1,.83),235:(0,.22,1,.93),236:(0,.10,1,.93),
 247:(0,.16,1,.91),248:(0,0,1,.79),249:(0,0,1,.80),258:(0,0,1,1),259:(0,0,1,.80),281:(0,0,1,.76),282:(0,.13,1,.94),291:(0,0,1,.80),292:(0,.10,1,.94),
 303:(0,0,1,.79),304:(0,.10,1,.82),316:(0,.10,1,.94),317:(0,.10,1,.94),326:(0,.10,1,.94),328:(0,.10,1,.94),342:(0,.10,1,.94),343:(0,.10,1,.94),
 352:(0,.10,1,.94),353:(0,.11,1,1),354:(0,.10,1,.94),363:(0,.10,1,.94),364:(0,.10,1,.94),365:(0,.10,1,.94),376:(0,.10,1,.94),377:(0,.10,1,.94),
 386:(0,.10,1,.86),387:(0,.10,1,.94),388:(0,.10,1,.94),397:(0,.10,1,.98),399:(0,0,1,1),414:(0,.10,1,.94),415:(0,.10,1,.94),416:(0,.10,1,.94),
 424:(0,0,1,.94),425:(0,.10,1,.94),426:(0,.10,1,.94),437:(0,.12,1,.87),439:(0,.10,1,.86),440:(0,0,.93,.97),442:(.09,0,.975,1)}
 changes=[]
 for id,r in report['records'].items():
  old=dict(r);num=int(id)
  key=replacements.get(num)
  if key:
   a=next(a for a in candidates if a['key']==key and a['season']==r['season'] and a['essence']==r['wikiEssence'])
   raw=(ROOT/a['file']).read_bytes();dest=ROOT/'public/season-art'/(a['sha256']+Path(key).suffix.lower());dest.write_bytes(raw)
   r.update({k:a[k] for k in ['alt','filePage','key','section','src','subsection','originalUrl','width','height','bytes','sha256']})
   r.update(url='/season-art/'+dest.name,downloadUrl=a['originalUrl'],presentation='poster')
  viewport=crops.get(num,(0,0,1,1))
  if r['presentation']=='strip':viewport=(.80 if r['wikiEssence']==5 else .56,0,1,1)
  if r['season']==1 and r['wikiEssence']==6:viewport=(0,0,1,.64)
  if num in (115,183,235,247,441):
   stem={115:'s11e1',183:'s16e3',235:'s21e1',247:'s22e1',441:'s39e2'}[num];source_key={115:'S11E1Poster.jpg',183:'S16E3Poster.png',235:'S21E1Poster.jpg',247:'S22E1Poster.jpg',441:'S39E2Poster.jpg'}[num];p=ROOT/f'public/season-art/{stem}-clean.png';raw=p.read_bytes();im=Image.open(p)
   r.update(url=f'/season-art/{stem}-clean.png',sha256=hashlib.sha256(raw).hexdigest(),width=im.width,height=im.height,bytes=len(raw),origin='wiki-reference-edited',presentation='poster')
   r['edit']={'method':'imagegen localized text/logo removal','sourceUrl':next(a['originalUrl'] for a in candidates if a['key']==source_key),'sourceSha256':next(a['sha256'] for a in candidates if a['key']==source_key),'outputSha256':r['sha256']}
   viewport=(0,0,1,1)
  supplied=read(OUT/'user-s6e2.json') if num==63 else read(OUT/'user-season-art.json')['records'].get(id)
  if supplied:
   p=ROOT/supplied['file'];raw=p.read_bytes();im=Image.open(p)
   if hashlib.sha256(raw).hexdigest()!=supplied['sha256']:raise ValueError('User artwork hash mismatch')
   season=supplied.get('season',r['season']);essence=supplied.get('essence',r['wikiEssence']);dest=ROOT/'public/season-art'/(f's{season}e{essence}-'+supplied['sha256']+'.png');dest.write_bytes(raw)
   r.update(url='/season-art/'+dest.name,sha256=supplied['sha256'],width=im.width,height=im.height,bytes=len(raw),origin='user-provided',key=f'S{season}E{essence}UserArtwork.png',filePage='',context='',originalUrl='',downloadUrl='',src='',alt=f'Season {season} Essence {essence} artwork supplied by user',presentation='poster')
   r['suppliedByUser']=True;viewport=(0,0,1,1)
  # Aliases share exactly the same image and viewport as their representative.
  r['viewport']=viewport
  changes.append(dict(id=id,oldUrl=old['url'],url=r['url'],key=r['key'],viewport=viewport,replaced=old['url']!=r['url']))
 representatives={ (r['season'],r['wikiEssence']):r for id,r in report['records'].items() if int(id)<1000 }
 for id,r in list(report['records'].items()):
  if int(id)>=1000 and int(id)!=134001:
   rep=representatives.get((r['season'],r['wikiEssence']))
   if rep:report['records'][id]={**rep,'boxId':id,'name':r['name']}
 report['presentationRevision']='clean-art-v1';source.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
 (OUT/'clean-art-selection.json').write_text(json.dumps(dict(changes=changes,limits=['Presentation crops omit branded margins; original bytes remain preserved.','S11E1, S16E3, S21E1, S22E1 and S39E2 are AI-edited derivatives, not recovered native assets.']),indent=2),encoding='utf8')
 print(json.dumps(dict(records=len(report['records']),replaced=sum(c['replaced'] for c in changes))))
if __name__=='__main__':main()
