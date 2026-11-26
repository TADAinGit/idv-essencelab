"""Export result background/owned source evidence without executing game scripts."""
import importlib.util,json,types
from pathlib import Path
from PIL import Image,ImageDraw
from extract_gacha_ui import ROOT,CFG,EXTRACTOR,EssenceResourceStore,image_decode,sha,write_json,walk
def main():
 out=ROOT/'public/game-results';evidence=ROOT/'research/ui-polish'
 store=EssenceResourceStore(Path(CFG['analysis'])/'resources.sqlite',CFG['game'],evidence/'payloads')
 spec=importlib.util.spec_from_file_location('polish_csb_parser',EXTRACTOR/'gui/widgets/viewers/cocos_viewer/cocos_parser.py')
 parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
 records=[];bindings=[]
 for name in ['treasure_open_ten_ani','treasure_open_item','common_get_item']:
  raw,stamp=store.read('ui/dm65ui/res/'+name+'.csb');p=parser.CocosBinaryParser(types.SimpleNamespace(data=raw));tree=p.parse_node(p.reader.table(p.reader.root(),10))
  write_json(evidence/(name+'.nodes.json'),dict(source=stamp,root=tree))
  for path,n in walk(tree):
   if any(t in n['name'].lower() for t in ['bg','light','own','have','repeat']):
    r=n.get('details',{}).get('resource',{})
    bindings.append(dict(csb=name,node=path,resource=r,position=n['position'],size=n['size'],anchor=n['anchorPoint'],color=n['color']))
    if r.get('path') and not r.get('plist'):records.append(('ui/dm65ui/res/'+r['path'],name,path))
 records.append(('ui/dm65ui/res/common/tag_owned.dds',None,None))
 assets={};failures=[]
 for uri,csb,node in records:
  if uri in assets:continue
  try:
   resolved=uri if store.lookup(uri) else uri.rsplit('.',1)[0]+'.dds'
   raw,stamp=store.read(resolved);im=image_decode(raw)
   filename='owned.png' if 'tag_owned' in uri else 'source-'+Path(uri).stem+'.png'
   path=out/filename;im.save(path)
   assets[uri]=dict(url='/game-results/'+filename,width=im.width,height=im.height,sha256=sha(path.read_bytes()),source=stamp,csb=csb,node=node)
  except (ValueError,OSError) as ex:failures.append(dict(uri=uri,error=str(ex)))
 write_json(evidence/'result-source.json',dict(assets=assets,bindings=bindings,failures=failures))
 sheet=Image.new('RGB',(1200,((len(assets)+3)//4)*220),'#302a30');d=ImageDraw.Draw(sheet)
 for i,(uri,a) in enumerate(assets.items()):
  im=Image.open(ROOT/('public'+a['url']));im.thumbnail((290,185));x=(i%4)*300;y=(i//4)*220;sheet.paste(im,(x,y),im);d.text((x,y+185),Path(uri).name,fill='white')
 sheet.save(evidence/'result-sources.jpg')
 store.close();print(json.dumps(dict(assets=len(assets),failures=failures)))
if __name__=='__main__':main()
