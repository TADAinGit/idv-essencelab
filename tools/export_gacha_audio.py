"""Convert verified Wwise gacha media using the installed NeoXtractor codec.

Consumes retained bounded bank extraction and canonical asset-run receipts.
No game script is imported or executed. Raw banks/receipts remain private.
"""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CFG=json.loads((ROOT/'config.local.json').read_text(encoding='utf8'))
sys.path.insert(0,CFG['extractor'])
from core.wem import probe,to_ogg
from core.wem.bnk import extract_wem_media
from id5mapping.wwise.bank_scan import BankDatabase
from id5mapping.wwise.index_builder import load_binary_events

def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf8'))
def main():
 evidence=ROOT/'research/gacha-audio';out=ROOT/'public/game-audio';out.mkdir(exist_ok=True)
 receipt=read(evidence/'main-bank-bounded/resource.json');bank=Path(receipt['output']).read_bytes()
 assert len(bank)<=64*1024*1024 and sha(bank)==receipt['sha256']
 db=BankDatabase();db.add_bank_bytes(bank,'dwrg');assert db.version==135
 inline=dict(extract_wem_media(bank))
 index=Path(CFG['extractor'])/'id5mapping/wwise/wwise_event_hash_index.bin'
 names=load_binary_events(str(index));assets={}
 for key,event,folder in [('click','P_dwrg_ui2_ui_box_open',None),('one','P_dwrg_ui2_ui_box_one','wem-one'),('ten','P_dwrg_ui2_ui_box_ten','wem-ten')]:
  event_id=next(k for k,v in names.items() if v==event);sources=sorted(db.sources(event_id));assert len(sources)==1
  sid=sources[0]
  if folder:
   run=evidence/folder;assert read(run/'result.json')['status']=='passed'
   source=read(run/'payload/resource.json');assert source['path']==f'wwise/{sid}.wem'
   raw=Path(source['output']).read_bytes();assert sha(raw)==source['sha256']
  else:
   raw=inline[sid];source=dict(bankSha256=receipt['sha256'],inlineMediaId=sid)
  assert len(raw)<2*1024*1024
  info=probe(raw);assert info.codec=='vorbis' and info.channels==2 and info.sample_rate==44100
  audio=to_ogg(raw);digest=sha(audio);name=f'{key}-{digest[:16]}.ogg';(out/name).write_bytes(audio)
  assets[key]=dict(url='/game-audio/'+name,sha256=digest,bytes=len(audio),duration=info.duration_samples/info.sample_rate,event=event,eventId=event_id,mediaId=sid,sourceSha256=sha(raw),source=source)
 public={key:{k:v for k,v in row.items() if k in ['url','sha256','duration']} for key,row in assets.items()}
 (out/'manifest.js').write_text('export const gachaSounds='+json.dumps(public,separators=(',',':'))+';\n',encoding='utf8')
 report=dict(assets=assets,bank=receipt,eventIndexSha256=sha(index.read_bytes()),codecSha256=sha((Path(CFG['extractor'])/'core/wem/vorbis.py').read_bytes()),toolSha256=sha(Path(__file__).read_bytes()),limits=['Original composite opening audio includes streak and burst; no synthetic replacements.','Browser timing follows the existing CSB adapter, not a full native Wwise mix.'])
 (evidence/'export.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(public,indent=2))
if __name__=='__main__':main()
