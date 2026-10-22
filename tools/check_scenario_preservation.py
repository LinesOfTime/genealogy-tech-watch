"""Read-only review of the current scenario batch against HEAD, before commit."""
import copy
import json
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[1]
for file,fields in [('catalog.json',('use_case','limitations','editorial_corrections')),
                    ('docs/research.json',('editorial_use_case','editorial_limitations','editorial_corrections'))]:
    old=json.loads(subprocess.check_output(['git','show','HEAD:'+file],cwd=root))
    new=json.loads((root/file).read_text(encoding='utf-8'))
    if isinstance(old,list):
        assert [x['name'] for x in old]==[x['name'] for x in new]
        old={x['name'].lower():x for x in old};new={x['name'].lower():x for x in new}
    assert old.keys()==new.keys()
    changed=[]
    for key in old:
        if old[key]==new[key]:continue
        before,after=copy.deepcopy(old[key]),copy.deepcopy(new[key])
        for field in fields:before.pop(field,None);after.pop(field,None)
        assert before==after,key
        previous=old[key].get('editorial_corrections',[])
        corrections=new[key]['editorial_corrections']
        assert corrections[:len(previous)]==previous,key
        assert len(corrections)==len(previous)+1,key
        snapshot=corrections[-1]['previous_catalog' if file=='catalog.json' else 'previous_research']
        for field,value in snapshot.items():assert old[key].get(field)==value,(key,field)
        changed.append(key)
    print(file,':',len(changed),'cards; unrelated fields preserved')
