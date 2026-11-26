import test from 'node:test';
import assert from 'node:assert/strict';
import {collectionItems} from '../public/collection-filters.js';

test('collection filters compose search and grade, with numeric ID and grade sorting before pagination',()=>{
 const collection={'1:100':2,'1:9':1,'1:20':1,'5:9':1};
 const rewards={'1:100':{id:100,type:1,quality:4,name:'Đỏ',typeName:'Trang phục'},'1:9':{id:9,type:1,quality:5,name:'Vàng',typeName:'Trang phục'},'1:20':{id:20,type:1,quality:4,name:'Đen',typeName:'Trang phục'},'5:9':{id:9,type:5,quality:3,name:'Đỏ',typeName:'Phụ kiện'}};
 const before=JSON.stringify(collection);
 const list=options=>collectionItems(collection,rewards,options);
 assert.deepEqual(list(),Object.keys(collection));
 assert.deepEqual(list({sort:'id-asc'}),['1:9','5:9','1:20','1:100']);
 assert.deepEqual(list({sort:'id-desc'}),['1:100','1:20','5:9','1:9']);
 assert.deepEqual(list({sort:'grade-desc'}),['1:9','1:20','1:100','5:9']);
 assert.deepEqual(list({sort:'grade-asc'}),['5:9','1:20','1:100','1:9']);
 assert.deepEqual(list({query:'do',grade:'4',sort:'id-asc'}),['1:100']);
 assert.deepEqual(list({grade:'6'}),[]);
 assert.equal(JSON.stringify(collection),before);
});
