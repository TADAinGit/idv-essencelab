"""Read reward widget trees and exact resource/font payloads as bounded data."""
import importlib.util
import json
from pathlib import Path
from extract_gacha_ui import ROOT, CFG, EXTRACTOR, EssenceResourceStore, image_decode, sha, write_json, walk

def main():
    evidence = ROOT / 'research/reward-widgets'
    out = ROOT / 'public/game-rewards'
    out.mkdir(parents=True, exist_ok=True)
    store = EssenceResourceStore(Path(CFG['analysis'])/'resources.sqlite', CFG['game'], evidence/'payloads')
    parser_path = EXTRACTOR/'gui/widgets/viewers/cocos_viewer/cocos_parser.py'
    spec = importlib.util.spec_from_file_location('reward_widget_parser', parser_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = dict(widgets={}, textures={}, fonts={})
    names = ['common_get_item','item_common_skin','item_common_char','item_common_decorate','item_common_motion','item_common_paint','item_common_emoticon','item_common_coin','item_common_mark','item_common_frame_o_doodle','item_common_tags','treasure_item','common_face','common_face_cover','item_common_pose','item_common_pet','item_common_bgm','item_common_furniture']
    for name in names:
        uri = 'ui/dm65ui/res/' + name + '.csb'
        raw, stamp = store.read(uri)
        class Source:
            data = raw
            def __str__(self):
                return uri
        parser = module.CocosBinaryParser(Source())
        tree = parser.parse_node(parser.reader.table(parser.reader.root(), 10))
        write_json(evidence/(name+'.json'), tree)
        bindings = []
        for path, node in walk(tree):
            for field in ['resource','normalResource','projectFile','fontResource']:
                res = node.get('details',{}).get(field)
                literal = res.get('path') if isinstance(res,dict) else res
                if not literal:
                    continue
                bindings.append(dict(node=path, field=field, resource=res, size=node.get('size'), position=node.get('position'), scale=node.get('scale'), color=node.get('color')))
                if field not in ['resource','normalResource'] or not literal.lower().endswith(('.png','.dds')):
                    continue
                full = literal if literal.startswith('ui/') else 'ui/dm65ui/res/'+literal
                if full in report['textures']:
                    continue
                try:
                    resolved = full if store.lookup(full) else full.rsplit('.',1)[0]+'.dds'
                    pixels, receipt = store.read(resolved)
                    image = image_decode(pixels)
                    dest = out/(Path(literal).stem+'-'+sha(pixels)[:10]+'.png')
                    image.save(dest)
                    report['textures'][full] = dict(url='/game-rewards/'+dest.name, resolved=resolved, width=image.width, height=image.height, sha256=sha(dest.read_bytes()), provenance=receipt)
                except (OSError, ValueError) as exc:
                    report['textures'][full] = dict(error=str(exc))
        report['widgets'][name] = dict(provenance=stamp, bindings=bindings)
    for name in ['pop1w5.ttc','font_en.ttf','font_en2.ttc','font_d5.ttf','roboto-medium.ttf']:
        uri = 'ui/dm65ui/res/font/'+name
        raw, stamp = store.read(uri)
        suffix = '.ttf' if raw[:4] == b'\x00\x01\x00\x00' else '.ttc'
        dest = evidence/('font-'+Path(name).stem+suffix)
        dest.write_bytes(raw)
        report['fonts'][name] = dict(file=str(dest), provenance=stamp, signature=raw[:4].hex())
    store.close()
    write_json(evidence/'audit.json',report)
    print(json.dumps(dict(widgets=len(report['widgets']), textures=len(report['textures']), fonts=len(report['fonts']))))

if __name__ == '__main__':
    main()
