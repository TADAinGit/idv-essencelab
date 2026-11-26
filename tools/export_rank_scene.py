"""Export authored Rank curtain and source timeline layout; no game execution."""
import importlib.util
import json
import types
from pathlib import Path
from PIL import Image
from extract_gacha_ui import ROOT,CFG,EXTRACTOR,EssenceResourceStore,image_decode,sha,write_json,walk

def main():
    evidence=ROOT/'research/rank-screen';out=ROOT/'public/game-rank';out.mkdir(exist_ok=True)
    store=EssenceResourceStore(Path(CFG['analysis'])/'resources.sqlite',CFG['game'],evidence/'payloads')
    spec=importlib.util.spec_from_file_location('rank_scene_parser',EXTRACTOR/'gui/widgets/viewers/cocos_viewer/cocos_parser.py')
    parser=importlib.util.module_from_spec(spec);spec.loader.exec_module(parser)
    sources={};trees={}
    for name in ['treasure_list_content','treasure_list_show']:
        raw,receipt=store.read('ui/dm65ui/res/'+name+'.csb')
        p=parser.CocosBinaryParser(types.SimpleNamespace(data=raw))
        if name=='treasure_list_show':doc=p.parse();tree=doc['root']
        else:tree=p.parse_node(p.reader.table(p.reader.root(),10))
        trees[name]=tree;sources[name]=receipt
    bindings=dict(walk(trees['treasure_list_content']))
    path='/Node/p_main/p_move/p_content/p_main/p_mask/p_treasure/img_bg'
    literal=bindings[path]['details']['resource']['path'];uri='ui/dm65ui/res/'+literal
    resolved=uri if store.lookup(uri) else uri[:-4]+'.dds';raw,stamp=store.read(resolved)
    image=image_decode(raw);target=out/'curtain.png';image.save(target)
    assets={'curtain':dict(url='/game-rank/curtain.png',requested=uri,resolved=resolved,node=path,csb='treasure_list_content.csb',sha256=sha(target.read_bytes()),source=stamp)}
    positions=[]
    node_map=dict(walk(trees['treasure_list_show']))
    for i in range(1,4):
        n=node_map[f'/Node/p_treasure_rank/p_n_item_{i}'];state={}
        for prop in ['Position','Scale','RotationSkew']:
            track=next(t for t in doc['animation']['timelines'] if t['actionTag']==n['actionTag'] and t['property']==prop)
            state[prop]=next(f['value'] for f in track['frames'] if f['frameIndex']==20)
        positions.append(dict(slot=i,actionTag=n['actionTag'],frame=20,state=state))
    # Tint the source ray texture using the existing gold/blue color binding;
    # this is a browser color adapter, not an authored replacement texture.
    ray=ROOT/'public/game-results/quality-45.png';original=Image.open(ray).convert('RGBA')
    palette={'gold':(255,248,45),'blue':(58,225,255)}
    for name,rgb in palette.items():
        r,g,b,a=original.split();gray=original.convert('L')
        tinted=Image.merge('RGBA',tuple(gray.point(lambda v,c=c:round(v*c/255)) for c in rgb)+(a,))
        dest=out/('result-rays-'+name+'.png');tinted.save(dest)
        assets['rays-'+name]=dict(url='/game-rank/'+dest.name,sha256=sha(dest.read_bytes()),sourceFile='public/game-results/quality-45.png',sourceSha256=sha(ray.read_bytes()),color=rgb,method='source luminance multiplied by source controller RGB, original alpha preserved')
    write_json(evidence/'scene-export.json',dict(assets=assets,sources=sources,slots=positions,
        toolSha256=sha(Path(__file__).read_bytes()),limits=['Static frame20 layout sampled; full native movement/material parity not claimed.','Result-ray tint is a browser adaptation from source pixels and controller palette.']))
    write_json(out/'scene.json',dict(curtain=assets['curtain']['url'],slots=positions,
        themes={name:assets['rays-'+name]['url'] for name in palette}))
    store.close();print(json.dumps(dict(assets=len(assets),slots=positions)))

if __name__=='__main__':main()
