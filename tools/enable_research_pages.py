#!/usr/bin/env python3
"""One-time integration into the existing static GitHub Pages checkout."""
from pathlib import Path
import re
root=Path(__file__).resolve().parent.parent
page=root/'docs'/'index.html'
s=page.read_text(encoding='utf-8')
if 'project.html?repo=' in s:
 print('Project detail links already installed');raise SystemExit(0)
# Add a research page link to every catalogue card, beside its heading.
needle='<h2><a target="_blank" rel="noopener noreferrer" href="${esc(x.url)}">${esc(x.name)} ↗</a></h2>'
if needle not in s:raise SystemExit('Unknown index.html structure; no files changed. Update integration pattern manually.')
s=s.replace(needle,needle+'<p class="muted"><a href="project.html?repo=${encodeURIComponent(x.name)}">Подробное исследование →</a></p>')
page.write_text(s,encoding='utf-8')
import shutil
for name in ('catalog.json','digest.json'):
 source=root/name
 if not source.exists():raise SystemExit('Missing '+str(source))
 shutil.copyfile(source,root/'docs'/name)
project=root/'docs'/'project.html'
project.write_text(project.read_text(encoding='utf-8').replace("fetch('../catalog.json')","fetch('catalog.json')").replace("fetch('../digest.json')","fetch('digest.json')"),encoding='utf-8')
print('Updated docs/index.html; research pages available for catalogue projects.')
