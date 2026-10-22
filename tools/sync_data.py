from pathlib import Path
import json,re
root=Path(__file__).resolve().parents[1]
for stem,source in (("index","catalog"),("digest","digest")):
    p=root/"docs"/(stem+".html")
    data=json.loads((root/(source+".json")).read_text(encoding="utf-8"))
    payload=json.dumps(data,ensure_ascii=False,separators=(",",":")).replace("</", "<\\/")
    text=p.read_text(encoding="utf-8")
    updated,n=re.subn(r'(<script id="seed" type="application/json">).*?(</script>)',lambda m:m.group(1)+payload+m.group(2),text,count=1,flags=re.S)
    if n!=1:raise SystemExit(f"Cannot find embedded seed in {p}")
    p.write_text(updated,encoding="utf-8")
    print(f"Synced {source}.json -> {p}")
