import {readdir,readFile,writeFile,mkdir,copyFile,rm,lstat,realpath} from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
export const PROJECT='idv-essencelab';
export const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const webExtensions=new Set(['.html','.js','.css','.json','.svg','.png','.webp','.jpg','.jpeg','.ico','.ttf','.woff','.woff2','.ogg','.wav']);
const textExtensions=new Set(['.html','.js','.css','.json','.svg']);
const blocked=p=>p.startsWith('assets/')||p.startsWith('source-data/')||p.startsWith('research/')||p==='config.local.json'||(p.startsWith('data/')&&!/^data\/v2\/(?:index\.json$|reward-index\.json$|boxes\/\d+\.json$|rewards\/\d+-\d+\.json$)/.test(p));
const posix=p=>p.split(path.sep).join('/');
async function regular(file){try{const info=await lstat(file);return info.isFile()&&!info.isSymbolicLink();}catch{return false;}}
export async function buildPages(root=ROOT){
 root=await realpath(root);const source=path.join(root,'public'),deploy=path.join(root,'.deploy'),output=path.join(deploy,'pages');
 for(const dir of [deploy,output]){try{if((await lstat(dir)).isSymbolicLink())throw Error('Refusing linked deploy directory: '+dir);}catch(error){if(error.code!=='ENOENT')throw error;}}
 // Resolve and verify the exact generated target before any recursive removal.
 if(path.resolve(output)!==path.join(root,'.deploy','pages'))throw Error('Unsafe deploy output');
 await mkdir(deploy,{recursive:true});await rm(output,{recursive:true,force:true});await mkdir(output,{recursive:true});
 const selected=new Set(),pending=[],records=[],omitted=new Set();
 function enqueue(relative){relative=posix(path.normalize(relative));if(relative.startsWith('../')||path.isAbsolute(relative)||blocked(relative)){omitted.add(relative);return;}if(!selected.has(relative)){selected.add(relative);pending.push(relative);}}
 for(const entry of await readdir(source,{withFileTypes:true}))if(entry.isFile()&&/\.(?:js|css|html)$/.test(entry.name))enqueue(entry.name);
 for(const folder of ['boxes','rewards'])for(const entry of await readdir(path.join(source,'data/v2',folder)))if(entry.endsWith('.json'))enqueue(`data/v2/${folder}/${entry}`);
 for(const item of ['data/v2/index.json','data/v2/reward-index.json','game-ui/skin.json','game-rewards/skin.json','game-rank/scene.json','game-fx/opening.json'])enqueue(item);
 while(pending.length){
  const relative=pending.shift(),file=path.join(source,relative),ext=path.extname(relative).toLowerCase();
  if(!webExtensions.has(ext)||!await regular(file))throw Error('Missing or unsafe runtime resource: '+relative);
  let data=await readFile(file);
  // Runtime projections omit export provenance and local research tool paths.
  const fields={'game-ui/skin.json':['schemaVersion','assets'],'game-rewards/skin.json':['widgets','perItem','palette'],'game-fx/opening.json':['schemaVersion','documents','assets','playback','capabilities']};
  if(fields[relative]){const value=JSON.parse(data);data=Buffer.from(JSON.stringify(Object.fromEntries(fields[relative].map(key=>[key,value[key]]))));}

  if(data.length>25*1024*1024)throw Error('Pages file exceeds25MiB: '+relative);
  if(textExtensions.has(ext)){
   const text=data.toString('utf8');
   if(/(?:[A-Za-z]:[\\/](?:Users|IdentityV-Research)|oauth_token|CLOUDFLARE_API_TOKEN\s*=)/i.test(text))throw Error('Private path or credential marker in '+relative);
   const candidates=[...text.matchAll(/"([^"\r\n]*)"|'([^'\r\n]*)'|`([^`\r\n]*)`/g)].map(m=>m[1]??m[2]??m[3]);
   candidates.push(...[...text.matchAll(/url\(\s*([^)'"\s]+)\s*\)/g)].map(m=>m[1]));
   for(let value of candidates){
    if(/^(?:https?:|data:|#|\/\/)/i.test(value)||value.includes('${')||value.includes('\\'))continue;
    value=value.split(/[?#]/)[0];if(!webExtensions.has(path.extname(value).toLowerCase()))continue;
    if(value.startsWith('/'))enqueue(value.slice(1));
    else if(value.startsWith('./')||value.startsWith('../')||ext==='.svg'){
     const target=path.normalize(path.join(path.dirname(relative),value));
     if(await regular(path.join(source,target)))enqueue(target);
    }
   }
  }
  const target=path.join(output,relative);await mkdir(path.dirname(target),{recursive:true});await writeFile(target,data);
  records.push({path:relative,bytes:data.length,sha256:createHash('sha256').update(data).digest('hex')});
 }
 const generated={
  '_headers':`/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: no-referrer\n  X-Frame-Options: DENY\n  Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'\n  Permissions-Policy: camera=(), microphone=(), geolocation=()\n/media/*\n  Cache-Control: public, max-age=31536000, immutable\n/data/v2/*\n  Cache-Control: no-cache\n/*.js\n  Cache-Control: no-cache\n/*.css\n  Cache-Control: no-cache\n/\n  Cache-Control: no-cache\n/collection\n  Cache-Control: no-cache\n/history\n  Cache-Control: no-cache\n`,
  '_redirects':'/collection/ /collection 301\n/history/ /history 301\n',
  'collection.html':await readFile(path.join(source,'index.html'),'utf8'),
  'history.html':await readFile(path.join(source,'index.html'),'utf8'),
  '404.html':'<!doctype html><html lang="vi"><meta charset="utf-8"><title>Không tìm thấy · EssenceLab</title><body><h1>Không tìm thấy trang</h1><p><a href="/">Về EssenceLab</a></p></body></html>'
 };
 for(const [relative,text]of Object.entries(generated)){await writeFile(path.join(output,relative),text);records.push({path:relative,bytes:Buffer.byteLength(text),sha256:createHash('sha256').update(text).digest('hex')});}
 if(records.length>20000)throw Error('Pages Free exceeds20000 files');
 records.sort((a,b)=>a.path.localeCompare(b.path));
 const report={project:PROJECT,builtAt:new Date().toISOString(),files:records.length,bytes:records.reduce((sum,r)=>sum+r.bytes,0),manifestSha256:createHash('sha256').update(JSON.stringify(records)).digest('hex'),omittedReferences:[...omitted].sort(),records};
 await writeFile(path.join(deploy,'manifest.json'),JSON.stringify(report,null,2));
 return {output,...report};
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const report=await buildPages();console.log(JSON.stringify({project:report.project,output:report.output,files:report.files,bytes:report.bytes,manifestSha256:report.manifestSha256,omittedReferences:report.omittedReferences},null,2));
}
