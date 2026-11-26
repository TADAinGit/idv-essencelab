"""Export source-selected article/quality frames, without executing game code."""
import json
import shutil
from pathlib import Path
from extract_gacha_ui import ROOT, CFG, EssenceResourceStore, image_decode, sha, write_json

TYPES = {1:('CLOTH','item_common_skin','img_skin'), 2:('INDIVIDUAL_ACTION','item_common_motion','img_motion'),
         3:('WAIT_ACTION','item_common_pose','img_pose'), 4:('POSTER','item_common_paint','img_paint'),
         5:('DECORATION','item_common_decorate','img_decorate'), 6:('APPENDAGE','item_common_pet','img_pet'),
         7:('CHASE_MUSIC','item_common_bgm',None), 9:('FACE','common_face','img_face'),
         10:('FACE_FRAME','common_face_cover','img_cover'),14:('FURNITURE','item_common_furniture','img_furniture'),
         97:('TOKEN','item_common_coin','img_coin'),202:('OFFERINGS','item_common_mark','img_mark')}
QUALITY = dict(zip(['D','C','B','A','S','SS'],range(1,7)))

def quality_map(evidence):
    code = next(c for c in json.loads((evidence/'article-init/ir.json').read_text(encoding='utf8'))[0]['code_objects'] if c['qualname']=='UIArticleItem.__init__')
    stack=[]
    # Straight-line literal construction only. Unknown instruction aborts.
    for ins in code['instructions']:
        if not 3206 <= ins['offset'] <= 6538:
            continue
        op=ins['name']
        if op=='LOAD_GLOBAL': stack.append(ins['symbol'])
        elif op=='LOAD_ATTR': stack.append(stack.pop()+'.'+ins['symbol'])
        elif op=='LOAD_CONST': stack.append(code['constants'][ins['arg']])
        elif op=='BUILD_MAP':
            n=ins['arg']; pairs=stack[-2*n:]; del stack[-2*n:]
            stack.append(dict(zip(pairs[::2],pairs[1::2])))
        else: raise ValueError('Unsupported literal-map instruction: '+op)
    if len(stack)!=1: raise ValueError('Literal-map stack mismatch')
    return {key.rsplit('.',1)[1]:{QUALITY[q.rsplit('.',1)[1]]:v for q,v in value.items()} for key,value in stack[0].items()}

def main():
    evidence=ROOT/'research/reward-widgets';out=ROOT/'public/game-rewards';out.mkdir(parents=True,exist_ok=True)
    mappings=quality_map(evidence)
    timeline=json.loads((evidence/'quality-timeline.json').read_text(encoding='utf8'))
    quality_node=next(n for n in timeline['root']['children'] if n['name']=='quality_l')['children'][0]
    color_track=next(t for t in timeline['animation']['timelines'] if t['property']=='CColor' and t['actionTag']==quality_node['actionTag'])
    palette={}
    for letter,q in QUALITY.items():
        clip=next(c for c in timeline['animation']['clips'] if c['name']=='loop_'+letter.lower())
        color=next(f['value'] for f in color_track['frames'] if f['frameIndex']==clip['startIndex'])
        palette[str(q)]='#'+''.join(f"{color[k]:02x}" for k in ['r','g','b'])
    store=EssenceResourceStore(Path(CFG['analysis'])/'resources.sqlite',CFG['game'],evidence/'payloads')
    receipts={}; missing={}
    def texture(literal):
        if literal in receipts:return receipts[literal]['url']
        uri=literal if literal.startswith('ui/') else 'ui/dm65ui/res/'+literal
        try:
            resolved=uri if store.lookup(uri) else uri.rsplit('.',1)[0]+'.dds'
            raw,stamp=store.read(resolved);image=image_decode(raw)
            dest=out/(Path(literal).stem+'-'+sha(raw)[:10]+'.png');image.save(dest)
            receipts[literal]=dict(url='/game-rewards/'+dest.name,requested=uri,resolved=resolved,
                width=image.width,height=image.height,imageSha256=sha(dest.read_bytes()),provenance=stamp)
            return receipts[literal]['url']
        except (OSError,ValueError) as exc:
            missing[literal]=str(exc);return None
    def nodes(tree):
        result={tree['name']:tree}
        for child in tree.get('children',[]):result.update(nodes(child))
        return result
    widgets={}
    for typ,(enum,widget,icon_name) in TYPES.items():
        tree=json.loads((evidence/(widget+'.json')).read_text(encoding='utf8'));lookup=nodes(tree)
        frame=lookup.get('img_quality');icon=lookup.get(icon_name,{})
        frames={str(q):texture(path) for q,path in mappings.get(enum,{}).items()}
        if typ==9:
            frames={str(q):texture('common/bg_face_empty.png') for q in range(1,7)}
        if typ==14:
            # Common furniture branch; special function/category variants remain
            # explicit per-item overrides below when their source data is known.
            frames={str(q):texture('common/quality_furniture_'+letter.lower()+('_new' if q in (4,5) else '')+'.png') for letter,q in QUALITY.items()}
        if typ==97:
            frames={str(q):texture('common/quailty_common_'+letter.lower()+'.png') for letter,q in QUALITY.items()}
        size=(frame or {}).get('size',{'width':128,'height':126})
        width,height=size['width'],size['height']
        icon_size=icon.get('size',{'width':120,'height':120});icon_scale=icon.get('scale',{'x':1,'y':1})
        name=next((n for n in lookup.values() if n['name'] in ['text_skin_name','text_pose_name','text_bgm_name']),None)
        widgets[str(typ)]=dict(widget=widget,article=enum,width=width,height=height,
            iconWidth=icon_size['width']*icon_scale['x']/width*100,
            iconHeight=icon_size['height']*icon_scale['y']/height*100,
            frames=frames,showName=bool(name),nameY=50-name['position']['y']/height*100 if name else None,
            nameColor=('#'+''.join(f"{name.get('color',{}).get(c,255):02x}" for c in ['r','g','b'])) if name else '#ffffff')
    # Character costumes use the authored 0.84 scale; square types retain their
    # own native dimensions instead of receiving a generic portrait card.
    fixes={1:.84,2:1,3:1.1,4:1,5:1.1,6:1.1,7:1.25,9:1.07,10:1.07,14:1,97:1,202:1.25}
    for typ,w in widgets.items():w['displayScale']=fixes[int(typ)]
    catalog=json.loads((ROOT/'public/data/catalog.json').read_text(encoding='utf8'))
    function_map=json.loads((evidence/'furniture-function-map.json').read_text(encoding='utf8'))['subtypes']
    per_item={}
    for key,item in catalog['rewards'].items():
        if item['type']!=14:continue
        data=item['configuration'];q=item['quality'];letter=next(k.lower() for k,v in QUALITY.items() if v==q)
        if data.get('f_category')==[3]:literal='common/quality_furniture_i_'+letter+'.png'
        elif function_map.get(str(data.get('f_type')),0)==1:literal='common/quality_furniture_f_'+letter+'_new.png'
        else:literal='common/quality_furniture_'+letter+('_new' if q in (4,5) else '')+'.png'
        per_item[key]=dict(frame=texture(literal),basis='get_furniture_image_path',requested=literal)
    font_source=evidence/'font-vi-source.ttf';font_receipt=json.loads((evidence/'font-vi-source.json').read_text(encoding='utf8'))
    if sha(font_source.read_bytes())!=font_receipt['sha256']:raise ValueError('Vietnamese font source hash mismatch')
    shutil.copyfile(font_source,ROOT/'public/game-ui/font-vi.ttf')
    write_json(evidence/'skin-export.json',dict(widgets=widgets,perItem=per_item,palette=palette,textures=receipts,missing=missing,font=font_receipt,
        sourceIRSha256=sha((evidence/'article-init/ir.json').read_bytes()),limits=['BGM and face-frame previews already contain their authored frame pixels.','Particle animation and native shader parity are not established.']))
    write_json(out/'skin.json',dict(widgets=widgets,perItem=per_item,palette=palette,font=dict(url='/game-ui/font-vi.ttf',sha256=font_receipt['sha256']),
        textures={k:{f:v for f,v in r.items() if f!='provenance'} for k,r in receipts.items()}))
    store.close();print(json.dumps(dict(textures=len(receipts),missing=missing)))

if __name__=='__main__':main()
