"""Rebuild the simple native radial mask as SVG to avoid magnified raster edges."""
import hashlib,json,math
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
def main():
 source=ROOT/'public/game-results/source-glow_1.png';im=Image.open(source).convert('RGBA')
 cx=im.width/2;cy=im.height/2;radius=im.width*.32;n=7200
 samples=[]
 for i in range(n):
  angle=i*2*math.pi/n;x=round(cx+radius*math.cos(angle));y=round(cy+radius*math.sin(angle));r,g,b,a=im.getpixel((x,y));samples.append(max(r,g,b)*a/255)
 threshold=(max(samples)+min(samples))/2;on=[v>threshold for v in samples]
 starts=[i for i in range(n) if on[i] and not on[i-1]];wedges=[]
 for start in starts:
  end=start+1
  while on[end%n] and end-start<n:end+=1
  wedges.append((start*360/n,end*360/n))
 paths=[]
 for a,b in wedges:
  points=[(0,0)]+[(1800*math.cos(math.radians(t)),1800*math.sin(math.radians(t))) for t in (a,b)]
  paths.append('<path d="M'+ ' L'.join(f'{x:.3f},{y:.3f}' for x,y in points)+' Z"/>')
 svg='<svg xmlns="http://www.w3.org/2000/svg" width="2048" height="2048" viewBox="-1024 -1024 2048 2048"><defs><radialGradient id="fade"><stop stop-color="white"/><stop offset=".68" stop-color="white" stop-opacity=".85"/><stop offset="1" stop-color="white" stop-opacity="0"/></radialGradient><mask id="falloff"><circle r="1024" fill="url(#fade)"/></mask></defs><g fill="white" mask="url(#falloff)">'+''.join(paths)+'</g></svg>'
 dest=ROOT/'public/game-results/result-rays.svg';dest.write_text(svg,encoding='utf8')
 evidence=dict(sourceFile=str(source.relative_to(ROOT)),sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),outputSha256=hashlib.sha256(dest.read_bytes()).hexdigest(),wedges=wedges,method='Angular threshold trace at source radius32%; straight ray edges rebuilt in vector; smooth browser falloff.',limits=['Browser composition and palette, not native shader/render parity.'])
 (ROOT/'research/ui-polish/vector-rays.json').write_text(json.dumps(evidence,indent=2),encoding='utf8');print('Rays:',len(wedges))
if __name__=='__main__':main()
