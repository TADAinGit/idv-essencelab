"""Export the current Alice UI subtree with original pixels and CSB provenance."""
import base64,json,hashlib
from pathlib import Path
from extract_gacha_ui import image_decode,walk,sha
ROOT=Path(__file__).resolve().parents[1]
def main():
    out=ROOT/'public/game-scene';out.mkdir(exist_ok=True)
    tree=json.loads((ROOT/'research/game-ui/treasure_list_new.csb.nodes.json').read_text(encoding='utf-8'))
    avatar=next(n for p,n in walk(tree) if p=='/treasure/p_avatar/avatar_1')
    manifest=json.loads((ROOT/'assets/manifest.json').read_text(encoding='utf-8'))
    records={r['requested']:r for r in manifest['resources']};assets=[]
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1722" height="750" viewBox="0 0 1722 750"><g transform="translate(861 710) scale(1 -1)">']
    def draw(n):
        pos=n['position'];scale=n['scale'];a=n['anchorPoint'];size=n['size']
        if not n.get('visible',True) or not n.get('alpha',255):return
        rotation=n['rotationSkew'];assert abs(rotation['x']-rotation['y'])<.01
        svg.append(f'<g opacity="{n.get("alpha",255)/255}" transform="translate({pos["x"]} {pos["y"]}) rotate({rotation["x"]}) scale({scale["x"]} {scale["y"]}) translate({-a["x"]*size["width"]} {-a["y"]*size["height"]})">')
        uri=n.get('details',{}).get('resource',{}).get('path')
        if uri:
            uri='ui/dm65ui/res/'+uri;r=records[uri];raw=(ROOT/r['file']).read_bytes();assert sha(raw)==r['sha256']
            img=image_decode(raw);target=out/('alice-'+Path(uri).stem+'.png');img.save(target)
            data=base64.b64encode(target.read_bytes()).decode();svg.append(f'<image width="{size["width"]}" height="{size["height"]}" href="data:image/png;base64,{data}" transform="translate(0 {size["height"]}) scale(1 -1)"/>')
            assets.append(dict(uri=uri,sourceSha256=sha(raw),imageSha256=sha(target.read_bytes()),image='/game-scene/'+target.name,csbNode=n['name']))
        for c in n.get('children',[]):draw(c)
        svg.append('</g>')
    draw(avatar);svg.append('</g></svg>');(out/'alice-idle.svg').write_text(''.join(svg),encoding='utf-8')
    report=dict(avatar=avatar,assets=assets,canvas=dict(width=1722,height=750),source='treasure_list_new.csb',pose='authored setup avatar_1; current Alice',presentationYOffset=40,outputSha256=sha((out/'alice-idle.svg').read_bytes()))
    (ROOT/'research/game-screen/alice.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(parts=len(assets),sha256=report['outputSha256'])))
if __name__=='__main__':main()
