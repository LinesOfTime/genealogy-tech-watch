const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const context=vm.createContext({URL,structuredClone});
vm.runInContext(fs.readFileSync('docs/catalog-io.js','utf8'),context);
const validate=context.CatalogIO.validate;
const original=JSON.parse(fs.readFileSync('catalog.json','utf8'));
assert.equal(JSON.stringify(validate(original)),JSON.stringify(original));
const card={name:'test/project',url:'https://github.com/test/project',description:'<img src=x onerror=alert(1)>',custom:{kept:true}};
assert.equal(JSON.stringify(validate([card])),JSON.stringify([card]));
assert.throws(()=>validate({projects:[card]}));
assert.throws(()=>validate([{...card,url:'javascript:alert(1)'}]));
assert.throws(()=>validate([{...card,url:'https://github.com.evil.example/test/project'}]));
assert.throws(()=>validate([{...card,url:'https://user:password@github.com/test/project'}]));
assert.throws(()=>validate([card,{...card,name:'another',url:'https://www.github.com/Test/Project.git/'}]));
assert.throws(()=>validate([{...card,section:{html:'bad'}}]));
assert.throws(()=>validate([{...card,practical_priority:{priority:{unsafe:true}}}]));
assert.throws(()=>validate([{...card,legal_notes:{text:'Invalid'}}]));
assert.throws(()=>validate([{...card,legal_notes:[{label:'Legal',text:'Condition',checked_at:'2026-11-09',sources:[null]}]}]));
const research=JSON.parse(fs.readFileSync('docs/research.json','utf8'));
const before=JSON.stringify([original,research]);
const exported=context.CatalogIO.userExport(original.map(row=>({...row,research:research[row.name.toLowerCase()]??null})));
assert.equal(JSON.stringify([original,research]),before);
assert.equal(exported.length,original.length);
assert.equal(JSON.stringify(validate(exported)),JSON.stringify(exported));
function checkPublic(value){
  if(!value||typeof value!=='object')return;
  for(const [key,entry]of Object.entries(value)){
    assert.ok(!/approved_|approval_|_hash$|_sha256$/.test(key),key);
    assert.ok(!['reviewer','review_status','evidence_file','discovery_id','project_basis'].includes(key),key);
    checkPublic(entry);
  }
}
checkPublic(exported);
for(let i=0;i<original.length;i++){
  assert.equal(exported[i].description,original[i].description);
  assert.equal(exported[i].limitations,original[i].limitations);
  assert.equal(exported[i].research?.editorial_summary,research[original[i].name.toLowerCase()]?.editorial_summary);
  assert.equal(JSON.stringify(exported[i].history?.map(event=>event.change)),JSON.stringify(original[i].history?.map(event=>event.change)));
}
assert.equal(validate([]).length,0);
console.log('Catalog JSON IO passed: lossless object round-trip, unsafe URLs, duplicates and malformed fields rejected.');
