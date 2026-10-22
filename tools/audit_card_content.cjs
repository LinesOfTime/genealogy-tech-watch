/* Audit the exact selectors used by the project renderer; never edit research data. */
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..'),read=n=>fs.readFileSync(path.join(root,n),'utf8');
const c=JSON.parse(read('catalog.json')),r=JSON.parse(read('docs/research.json'));
const ctx=vm.createContext({URL});vm.runInContext(read('docs/watch-ui.js'),ctx);
const rows=c.map(x=>{
  const card=r[x.name.toLowerCase()]||{},selected=ctx.WatchUI.cardContent(x,card),flags=[];
  if(!selected.practical.text)flags.push('missing_practical');
  if(!selected.limitations.text)flags.push('missing_limitations');
  const raw=[x.limitations,card.audit_notes,card.editorial_limitations].filter(Boolean);
  if(raw.some(s=>/Часть\s*\d+|Ч\d+\s*:/i.test(s)))flags.push('service_notes_preserved');
  if(x.limitations&&card.audit_notes&&x.limitations===card.audit_notes)flags.push('duplicate_raw_notes');
  if(selected.limitations.text&&!/не\b|треб|огранич|провер|завис|предупреж|нельзя|необходим|лиценз|только|риск|отсутств|нуж|устарев|не /i.test(selected.limitations.text))flags.push('limitations_need_context_review');
  return {project:x.name,selected,flags};
});
const counts={};for(const row of rows)for(const flag of row.flags)counts[flag]=(counts[flag]||0)+1;
const report={method:'Exact shared presentation selectors. Flags are review prompts, not proof of factual error.',total:rows.length,counts,records:rows};
if(process.argv.includes('--write')){
  fs.writeFileSync(path.join(root,'reports/card-content-audit.json'),JSON.stringify(report,null,2)+'\n');
  let md='# Аудит практических сценариев и ограничений\n\nПроверены все '+rows.length+' карточки. Проверка использует те же правила выбора полей, что и интерфейс. Новые исследовательские факты не выводятся.\n\n'+Object.entries(counts).map(([k,v])=>'- '+k+': '+v).join('\n')+'\n\nСлужебные заметки и исходные дубли сохраняются в данных; интерфейс не выводит их дважды в основном блоке. limitations_need_context_review — эвристический сигнал: содержание требует прочтения, а не автоматической правки.\n\n';
  for(const row of rows.filter(x=>x.flags.includes('missing_practical')||x.flags.includes('missing_limitations')||x.flags.includes('limitations_need_context_review'))){md+='## '+row.project+'\n\n'+row.flags.join(', ')+'\n\n**Сценарий:** '+(row.selected.practical.text||'Не описан')+'\n\n**Ограничения:** '+(row.selected.limitations.text||'Не описаны')+'\n\n';}
  fs.writeFileSync(path.join(root,'reports/card-content-audit.md'),md.trimEnd()+'\n');
}
console.log(JSON.stringify({total:rows.length,counts,missing_practical:rows.filter(x=>x.flags.includes('missing_practical')).map(x=>({project:x.project,limitations:x.selected.limitations.text}))},null,2));
