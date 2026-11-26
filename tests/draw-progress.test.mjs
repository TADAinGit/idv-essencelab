import test from 'node:test';
import assert from 'node:assert/strict';
import {createState,drawBatch,profileKey} from '../public/engine.js';
import {drawProgress,progressCopy} from '../public/draw-progress.js';

test('progress follows the selected Essence/profile, actual rarity and shared guarantee counters',()=>{
 const box={id:'1',shareRateId:'shared',pools:{'4':[{key:'1:4'}],'5':[{key:'1:5'}]}},profile={weights:{'1':0,'2':0,'3':0,'4':100,'5':0},pity4:60,pity5:200};
 let state=createState();state=drawBatch(state,box,profile,10).state;
 const other={...box,id:'2'};state=drawBatch(state,other,profile,1).state;
 const custom={...profile,pity5:250};state=drawBatch(state,box,custom,1).state;
 const progress=drawProgress(state,box,profile,{'1:4':{quality:4}});
 assert.deepEqual(progress,{opened:10,s:0,a:10,remainingA:60,remainingS:189,partial:false});
 assert.equal(drawProgress(state,box,custom).opened,1);
 assert.match(progressCopy(progress),/10 vật phẩm bậc A/);
 assert.match(progressCopy(progress,'guarantee'),/A<\/span> trở lên/);
 assert.match(progressCopy(progress,'guarantee'),/189 lượt/);
 state.history[0].grade='5';
 assert.equal(drawProgress(state,box,custom,{'1:4':{quality:4}}).a,1);
 state.total=6000;
 assert.match(progressCopy(drawProgress(state,box,profile)),/Trong nhật ký gần đây/);
});

test('progress handles progressive pity, disabled guarantees and the next due draw',()=>{
 const box={id:'1',shareRateId:'1'},profile={kind:'user-default-v1',pity:{'4':60,'5':200}};
 const state=createState();state.counters[profileKey(box,profile)]={'4':24,'5':24};
 const progress=drawProgress(state,box,profile);
 assert.equal(progress.remainingA,36);assert.equal(progress.remainingS,176);
 const text=progressCopy(progress,'guarantee');
 assert.match(text,/progress-a">36 lượt/);assert.match(text,/progress-s">176 lượt/);
 state.counters[profileKey(box,profile)]['5']=200;
 assert.equal(drawProgress(state,box,profile).remainingS,1);
 const disabled=drawProgress(createState(),box,{weights:{},pity4:0,pity5:0});
 assert.equal(disabled.remainingA,null);assert.match(progressCopy(disabled,'guarantee'),/Chưa bật bảo hiểm/);
});
