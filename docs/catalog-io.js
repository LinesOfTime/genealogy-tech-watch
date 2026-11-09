/* Explicit local JSON preview. Never persist or replace the published catalogue. */
var CatalogIO = (() => {
  const scalarFields=['name','url','section','description','use_case','limitations','license','license_status','priority','origin','test_status'];
  function validate(value){
    if(!Array.isArray(value)||value.length>10000)throw Error('Ожидается массив не более 10 000 карточек.');
    const names=new Set(),urls=new Set();
    for(const [i,card] of value.entries()){
      if(!card||typeof card!=='object'||Array.isArray(card))throw Error(`Карточка ${i+1}: ожидается объект.`);
      for(const field of scalarFields)if(card[field]!==undefined&&typeof card[field]!=='string')throw Error(`Карточка ${i+1}: поле ${field} должно быть строкой.`);
      if(!card.name?.trim()||!card.url)throw Error(`Карточка ${i+1}: нужны name и url.`);
      let url;try{url=new URL(card.url)}catch{throw Error(`Карточка ${i+1}: неверный URL.`)}
      if(url.protocol!=='https:'||!['github.com','www.github.com','gitlab.com'].includes(url.hostname)||url.username||url.password||url.port||url.search||url.hash||!/^\/[\w.-]+(?:\/[\w.-]+)?\/?$/.test(url.pathname))throw Error(`Карточка ${i+1}: нужен безопасный HTTPS-адрес GitHub или GitLab.`);
      const identity=url.hostname.replace(/^www\./,'')+url.pathname.replace(/\/$/,'').replace(/\.git$/i,'').toLowerCase(),name=card.name.toLowerCase();
      if(names.has(name)||urls.has(identity))throw Error(`Карточка ${i+1}: повтор имени или адреса.`);
      names.add(name);urls.add(identity);
      if(card.practical_priority!==undefined){
        const p=card.practical_priority;
        if(!p||typeof p!=='object'||Array.isArray(p))throw Error(`Карточка ${i+1}: неверная практическая оценка.`);
        for(const key of ['priority','task','scope','rationale','evidence_level','review_status'])if(p[key]!==undefined&&typeof p[key]!=='string')throw Error(`Карточка ${i+1}: неверное поле оценки ${key}.`);
      }
      if(card.russia_applicability!==undefined&&(!card.russia_applicability||typeof card.russia_applicability!=='object'||Array.isArray(card.russia_applicability)))throw Error(`Карточка ${i+1}: неверная применимость.`);
      if(card.classification!==undefined){
        const value=card.classification;
        if(!value||typeof value!=='object'||Array.isArray(value)||typeof value.type_label!=='string'||
            !Array.isArray(value.domain_labels)||value.domain_labels.some(tag=>typeof tag!=='string'))throw Error('Неверная классификация.');
      }
      if(card.assessment_currency!==undefined){
        const value=card.assessment_currency;
        if(!value||typeof value!=='object'||Array.isArray(value)||typeof value.label!=='string'||
            [value.assessment_approved_at,value.last_substantive_source_check].some(date=>date!=null&&typeof date!=='string'))throw Error('Неверная актуальность оценки.');
      }
    }
    return structuredClone(value);
  }
  function bind({getData,setData,published}){
    const $=id=>document.getElementById(id),file=$('import-file'),status=$('json-status'),restore=$('restore-published');
    const exportButton=$('export-json');
    let preview=false,request=0,exporting=false;
    async function exportPublished(rows){
      const response=await fetch('research.json',{cache:'no-cache'});
      if(!response.ok)throw Error('Не удалось загрузить исследования.');
      const research=await response.json();
      if(!research||typeof research!=='object'||Array.isArray(research))throw Error('Неверный формат исследований.');
      return rows.map(card=>{
        const key=card.name.toLowerCase();
        const profile=Object.hasOwn(research,key)?research[key]:null;
        if(profile!==null&&(!profile||typeof profile!=='object'||Array.isArray(profile)))throw Error('Неверный формат исследования.');
        return {...card,research:profile};
      });
    }
    $('import-json').addEventListener('click',()=>file.click());
    file.addEventListener('change',async()=>{
      const current=++request,input=file.files?.[0];if(!input)return;
      try{
        if(input.size>10*1024*1024)throw Error('Файл больше 10 МиБ.');
        const rows=validate(JSON.parse((await input.text()).replace(/^\uFEFF/,'')));
        if(current!==request)return;
        setData(rows);preview=true;restore.hidden=false;
        exportButton.textContent='Экспорт локального JSON';
        status.textContent=`Локальный JSON: ${rows.length} карточек. Сведения файла не проверены и не опубликованы; расширенные исследования доступны только для опубликованных записей.`;
      }catch(error){if(current===request)status.textContent='Ошибка импорта: '+error.message+' Текущий каталог сохранён.'}
      finally{if(current===request)file.value=''}
    });
    restore.addEventListener('click',()=>{
      request++;setData(structuredClone(published));preview=false;restore.hidden=true;file.value='';
      exportButton.textContent='Экспорт с исследованиями';
      status.textContent='Опубликованный каталог восстановлен. Импорт не меняет данные сайта.';
    });
    exportButton.addEventListener('click',async()=>{
      if(exporting)return;
      const local=preview,current=request,rows=getData();
      exporting=true;
      exportButton.disabled=true;
      try{
        const data=local?rows:await exportPublished(rows);
        if(current!==request)return;
        const blob=new Blob([JSON.stringify(data,null,2)+'\n'],{type:'application/json;charset=utf-8'});
        const url=URL.createObjectURL(blob),a=document.createElement('a');
        a.href=url;
        a.download=local?'genealogy-tech-watch-local.json':'catalog-with-research.json';
        a.click();
        setTimeout(()=>URL.revokeObjectURL(url),1000);
        status.textContent=local?'Экспортирован локальный JSON.':'Экспортирован каталог с исследованиями.';
      }catch(error){
        if(current===request)status.textContent='Ошибка экспорта: '+error.message+' Повторите попытку.';
      }finally{
        exporting=false;
        exportButton.disabled=false;
      }
    });
  }
  return {validate,bind};
})();
