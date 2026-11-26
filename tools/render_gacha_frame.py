"""Rasterize source Spine setup meshes; no guessed border artwork."""
import json,math
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
def main():
 d=json.loads((ROOT/'research/game-screen/posed-frame.json').read_text());W,H=d['canvas']['width'],d['canvas']['height'];ox,oy=d['origin']['x'],d['origin']['y'];textures={}
 for name,slots in d['layers'].items():
  out=Image.new('RGBA',(W,H))
  for s in slots:
   if s['page'] not in textures:textures[s['page']]=Image.open(ROOT/'public/game-scene'/s['page']).convert('RGBA')
   original=textures[s['page']];src=Image.new('RGBA',original.size);x,y,w,h=s['crop'];src.paste(original.crop((x,y,x+w,y+h)),(x,y))
   layer=Image.new('RGBA',(W,H));v=s['vertices'];uv=s['uv'];dst=[(ox+v[i],H-oy-v[i+1]) for i in range(0,len(v),2)];st=[(uv[i]*s['width'],uv[i+1]*s['height']) for i in range(0,len(uv),2)]
   for k in range(0,len(s['triangles']),3):
    ids=s['triangles'][k:k+3];points=[dst[i] for i in ids];coords=[st[i] for i in ids];left=max(0,math.floor(min(x for x,y in points)));top=max(0,math.floor(min(y for x,y in points)));right=min(W,math.ceil(max(x for x,y in points)));bottom=min(H,math.ceil(max(y for x,y in points)))
    if right<=left or bottom<=top:continue
    (x0,y0),(x1,y1),(x2,y2)=points;det=(x1-x0)*(y2-y0)-(x2-x0)*(y1-y0)
    if abs(det)<1e-6:continue
    vals=[]
    for axis in [0,1]:
     q0,q1,q2=[c[axis] for c in coords];a=((q1-q0)*(y2-y0)-(q2-q0)*(y1-y0))/det;b=((x1-x0)*(q2-q0)-(x2-x0)*(q1-q0))/det;c=q0-a*x0-b*y0;vals.extend([a,b,c+a*left+b*top])
    patch=src.transform((right-left,bottom-top),Image.Transform.AFFINE,vals,Image.Resampling.BILINEAR)
    mask=Image.new('L',patch.size);ImageDraw.Draw(mask).polygon([(x-left,y-top) for x,y in points],fill=255);layer.paste(patch,(left,top),mask)
   if s['alpha']<1:layer.putalpha(layer.getchannel('A').point(lambda a:int(a*s['alpha'])))
   out.alpha_composite(layer)
  out.save(ROOT/'public/game-scene'/(name+'-posed.png'))
 print('rendered',W,H)
if __name__=='__main__':main()
