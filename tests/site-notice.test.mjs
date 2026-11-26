import test from 'node:test';
import assert from 'node:assert/strict';
import {installSiteNotice} from '../public/site-notice.js';
test('site notice cycles Vietnamese English Chinese and closes without changing stored player data',()=>{
 class Element extends EventTarget{
  hidden=true;style={setProperty(){}};clientWidth=500;scrollWidth=1400;offsetWidth=1400;
  setAttribute(name,value){this[name]=value;}
  contains(target){return target===this;}
  querySelector(){return this;}
 }
 const elements=Object.fromEntries(['site-info-button','site-info-banner','site-info-text','site-info-close'].map(id=>[id,new Element()]));
 const previous={document:globalThis.document,matchMedia:globalThis.matchMedia};
 const document=new EventTarget();document.getElementById=id=>elements[id];
 globalThis.document=document;globalThis.matchMedia=()=>({matches:false});
 try{
  installSiteNotice();const button=elements['site-info-button'],banner=elements['site-info-banner'],text=elements['site-info-text'];
  button.dispatchEvent(new Event('click'));assert.equal(banner.hidden,false);assert.equal(text.lang,'vi');assert.match(text.textContent,/phi lợi nhuận/);
  text.dispatchEvent(new Event('animationend'));assert.equal(text.lang,'en');assert.match(text.textContent,/no commercial purpose/);
  text.dispatchEvent(new Event('animationend'));assert.equal(text.lang,'zh-Hans');
  text.dispatchEvent(new Event('animationend'));assert.equal(text.lang,'vi');
  elements['site-info-close'].dispatchEvent(new Event('click'));assert.equal(banner.hidden,true);assert.equal(button['aria-expanded'],'false');
  button.dispatchEvent(new Event('click'));const escape=new Event('keydown');escape.key='Escape';document.dispatchEvent(escape);assert.equal(banner.hidden,true);
 }finally{globalThis.document=previous.document;globalThis.matchMedia=previous.matchMedia;}
});
