"""Bounded extraction of result-screen assets and their parsed CSB bindings."""
import importlib.util
import json
from pathlib import Path
from PIL import Image, ImageDraw
from extract_gacha_ui import ROOT, CFG, EXTRACTOR, EssenceResourceStore, image_decode, sha, write_json, walk


def main():
    out = ROOT / 'public/game-results'
    evidence = ROOT / 'research/game-results'
    out.mkdir(parents=True, exist_ok=True)
    evidence.mkdir(parents=True, exist_ok=True)
    store = EssenceResourceStore(Path(CFG['analysis']) / 'resources.sqlite', CFG['game'], evidence / 'payloads')
    store.output.mkdir(parents=True, exist_ok=True)
    parser_path = EXTRACTOR / 'gui/widgets/viewers/cocos_viewer/cocos_parser.py'
    spec = importlib.util.spec_from_file_location('result_csb_parser', parser_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sources, assets, failures = {}, {}, []

    def parse(name):
        uri = 'ui/dm65ui/res/' + name
        raw, stamp = store.read(uri)
        class Source:
            data = raw
            def __str__(self):
                return uri
        parser = module.CocosBinaryParser(Source())
        tree = parser.parse_node(parser.reader.table(parser.reader.root(), 10))
        sources[name] = stamp
        write_json(evidence / (name + '.nodes.json'), tree)
        return dict(walk(tree))

    nodes = parse('common_get_item_quality.csb')
    bindings = [('tool-label', 'system/treasure_new/img_bg_info.png', 'treasure_list_new.csb', '/treasure/p_operate/btn_content/img_bg_info'),
                ('confirm', 'system/treasure/btn_use_one_nml.png', 'treasure_open_ten_ani.csb', '/treasure_open/p_btn/btn_confirm'),
                ('again', 'system/treasure/btn_use_ten_nml.png', 'treasure_open_ten_ani.csb', '/treasure_open/p_btn/btn_open')]
    for index, (path, node) in enumerate(nodes.items()):
        for field in ['resource', 'normalResource']:
            uri = node.get('details', {}).get(field, {}).get('path')
            if uri:
                bindings.append(('quality-' + str(index), uri, 'common_get_item_quality.csb', path))
    # Candidate backdrop textures are retained with an explicit weaker binding.
    for name in ['bg_treasure_glow1', 'bg_treasure_glow2', 'bg_get_item', 'bg_quality']:
        bindings.append((name.replace('_', '-'), 'system/get_item/' + name + '.png', None, None))
    for key, literal, csb, node in bindings:
        uri = literal if literal.startswith('ui/') else 'ui/dm65ui/res/' + literal
        try:
            resolved = uri if store.lookup(uri) else uri.rsplit('.', 1)[0] + '.dds'
            raw, stamp = store.read(resolved)
            im = image_decode(raw)
            target = out / (key + '.png')
            im.save(target)
            assets[key] = dict(url='/game-results/' + target.name, requested=uri, resolved=resolved,
                               csb=csb, node=node, width=im.width, height=im.height,
                               imageSha256=sha(target.read_bytes()), provenance=stamp)
        except (OSError, ValueError) as exc:
            failures.append(dict(uri=uri, error=str(exc)))
    report = dict(assets=assets, sources=sources, failures=failures,
                  limits=['DDS candidates are not proof of native filename alias.',
                          'Backdrop candidates have no exact CSB binding; browser composition is an adaptation.'])
    write_json(out / 'assets.json', dict(assets={key: {k: v for k, v in asset.items() if k != 'provenance'} for key, asset in assets.items()}, limits=report['limits']))
    write_json(evidence / 'export.json', report)
    sheet = Image.new('RGB', (1000, ((len(assets)+4)//5)*180), '#29242b')
    draw = ImageDraw.Draw(sheet)
    for i, (key, a) in enumerate(assets.items()):
        im = Image.open(out / (key + '.png')).convert('RGBA')
        im.thumbnail((180, 140))
        x, y = (i%5)*200, (i//5)*180
        sheet.paste(im, (x+(180-im.width)//2, y), im)
        draw.text((x+3, y+145), key, fill='white')
    sheet.save(evidence / 'contact.png')
    store.close()
    print(json.dumps(dict(assets=len(assets), failures=failures)))


if __name__ == '__main__':
    main()
