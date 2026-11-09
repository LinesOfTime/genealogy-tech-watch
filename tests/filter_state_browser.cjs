/* Browser regression for URL filters, back navigation and mobile layout.
 * Requires Playwright and BROWSER_EXECUTABLE pointing to installed Chrome/Edge. */
const fs = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
(async () => {
  const browser = await chromium.launch({headless:true, executablePath:process.env.BROWSER_EXECUTABLE});
  try {
    const page = await browser.newPage({viewport:{width:375,height:812}});
    const runtimeErrors=[];
    page.on('pageerror',error=>runtimeErrors.push(error.message));
    page.on('console',message=>{if(message.type()==='error')runtimeErrors.push(message.text())});
    const root = path.resolve(__dirname,'../docs');
    await page.route('https://ux.local/**', async route => {
      const name = path.basename(new URL(route.request().url()).pathname) || 'index.html';
      const type = name.endsWith('.js') ? 'application/javascript' : name.endsWith('.css') ? 'text/css' : name.endsWith('.json') ? 'application/json' : 'text/html';
      await route.fulfill({body:await fs.readFile(path.join(root,name)),contentType:type});
    });
    await page.goto('https://ux.local/index.html',{waitUntil:'networkidle'});
    const published=JSON.parse(await fs.readFile(path.join(root,'catalog.json'),'utf8'));

    for (const repo of ['thodel/agentic_historian','rodoslovje/ged-merge','kjiwa/geneanet-drift','gramps-project/gramps-web']) {
      await page.locator('#search').fill(repo);
      const projectLink=page.locator('.card-links a[href="project.html?repo='+encodeURIComponent(repo)+'"]');
      assert.equal(await projectLink.count(),1);
      await projectLink.click();
      await page.waitForLoadState('networkidle');
      assert.equal((await page.locator('#title').innerText()).toLowerCase(),repo);
      const text=await page.locator('#content').innerText();
      assert.match(text,/Практическое применение/);
      if(repo==='thodel/agentic_historian') assert.match(text,/Бернского университета/);
      if(repo==='rodoslovje/ged-merge') assert.match(text,/словенском/);
      if(repo==='kjiwa/geneanet-drift') assert.match(text,/ViewPrivate/);
      if(repo==='gramps-project/gramps-web') assert.equal(text.split('Gramps Web 26.11.0–26.11.2:').length-1,1);
      await page.goto('https://ux.local/index.html',{waitUntil:'networkidle'});
    }
    await page.locator('#advanced-filters summary').click();
    const tags=['IIIF и просмотр изображений','OCR/HTR'];
    await page.locator('#domains').selectOption(tags);
    const expected=published.filter(card=>tags.every(tag=>card.classification.domain_labels.includes(tag)));
    assert.equal(await page.locator('.card').count(),expected.length);
    assert.equal(new URL(page.url()).searchParams.getAll('domains').length,tags.length);
    await page.reload({waitUntil:'networkidle'});
    assert.equal(await page.locator('.card').count(),expected.length);
    await page.locator('#reset-catalog').click();
    assert.equal(await page.locator('.card').count(),published.length);
    await page.locator('#advanced-filters').evaluate(element=>element.open=true);
    await page.locator('#currency').selectOption('Предложена новая оценка');
    assert.equal(await page.locator('.card').count(),published.filter(card=>card.assessment_currency.status==='proposed').length);
    await page.locator('#reset-catalog').click();
    await page.locator('#project-type').selectOption('Стандарт / спецификация');
    assert.equal(await page.locator('.card').count(),published.filter(card=>card.classification.primary_type==='standard').length);
    await page.locator('#reset-catalog').click();
    await page.locator('#advanced-filters').evaluate(element=>element.open=false);
    await page.locator('#search').fill('openheritageonline/agent-tooling');
    await page.locator('#advanced-filters summary').click();
    await page.locator('#editorial-priority').selectOption('P2');
    await page.locator('#priority').selectOption('Не оценён');
    assert.match(await page.locator('#shown').innerText(),/^Показано 1 из /);
    assert.match(await page.locator('.card').innerText(),/Предварительный приоритет · P2/);
    await page.locator('.card-links a[href^="project.html"]').click();
    await page.waitForLoadState('networkidle');
    const openHeritage = await page.locator('#content').innerText();
    for(const text of ['Archive Adapter','Research Workspace','Place Resolver/АТД','provenance/evidence',
      'только для поиска и чтения','Personal API','1.0.1','Не установлена']) {
      assert.ok(openHeritage.includes(text),text);
    }
    await page.goto('https://ux.local/index.html',{waitUntil:'networkidle'});
    await page.locator('#search').fill('Швейцария');
    assert.match(await page.locator('#shown').innerText(),/^Показано 1 из /);
    assert.match(await page.locator('.usage-geography').innerText(),/Швейцария.*e-periodica/);
    await page.locator('.card-links a[href^="project.html"]').click();
    await page.waitForLoadState('networkidle');
    assert.match(await page.locator('#content').innerText(),/не поиск по всем архивам Швейцарии/);
    await page.goto('https://ux.local/index.html',{waitUntil:'networkidle'});
    for(const repo of ['semanticmeaning/kinship-kit','joaquimrcarvalho/personal-historical-archive','kinprove/genealogy-research-recipes']){
      await page.locator('#search').fill(repo);
      assert.match(await page.locator('#shown').innerText(),/^Показано 1 из /);
      await page.locator('.card-links a[href^="project.html"]').click();
      await page.waitForLoadState('networkidle');
      assert.match(await page.locator('#content').innerText(),/Основания|Доказательность|уровень|E1/);
      if(repo.includes('kinship-kit'))assert.match(await page.locator('#content').innerText(),/бывшего СССР|Бывший СССР/);
      if(repo.includes('personal-historical'))assert.match(await page.locator('#content').innerText(),/Не установлена/);
      if(repo.includes('research-recipes'))assert.match(await page.locator('#content').innerText(),/1.10.0.*1.11.0/);
      await page.goto('https://ux.local/index.html',{waitUntil:'networkidle'});
    }
    const downloadEvent=page.waitForEvent('download');
    await page.locator('#export-json').click();
    const download=await downloadEvent;
    const downloaded=await download.createReadStream();
    const chunks=[];for await(const chunk of downloaded)chunks.push(chunk);
    const exported=JSON.parse(Buffer.concat(chunks).toString('utf8'));
    assert.equal(exported.length,JSON.parse(await fs.readFile(path.resolve(root,'catalog.json'),'utf8')).length);
    await page.locator('#import-file').setInputFiles({name:'local.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify([{name:'Local test',url:'https://github.com/example/local',description:'<img src=x onerror=alert(1)>'}]))});
    await page.waitForFunction(()=>document.getElementById('json-status').textContent.startsWith('Локальный JSON:'));
    assert.equal(await page.locator('.card').count(),1);
    assert.equal(await page.locator('.card img').count(),0);
    assert.match(await page.locator('#cards').innerText(),/Локальная запись/);
    await page.locator('#import-file').setInputFiles({name:'bad.json',mimeType:'application/json',buffer:Buffer.from('[{"name":"bad","url":"javascript:alert(1)"}]')});
    await page.waitForFunction(()=>document.getElementById('json-status').textContent.startsWith('Ошибка импорта:'));
    assert.equal(await page.locator('.card').count(),1);
    await page.locator('#restore-published').click();
    assert.equal(await page.locator('.card').count(),exported.length);
    await page.goto('https://ux.local/tasks.html?task=agents',{waitUntil:'networkidle'});
    for(const [country,repo] of [['Швеция','ai-riksarkivet/ra-mcp'],['Япония','itarunnn/jp-lit-mcp']]) {
      await page.locator('#query').fill(country);
      assert.equal(await page.locator('#results article').count(),1);
      assert.match(await page.locator('#results').innerText(),new RegExp(repo));
      assert.match(await page.locator('#results').innerText(),/Границы применения/);
      assert.match(await page.locator('#results').innerText(),/Проба на своих материалах/);
      assert.match(await page.locator('#results').innerText(),/утверждён пользователем/);
      await page.locator('#results [data-compare]').click();
    }
    assert.match(await page.locator('#compare-results').innerText(),/География источников/);
    await page.goto('https://ux.local/project.html?repo=genealogy-mcp%2Fgramps-mcp',{waitUntil:'networkidle'});
    assert.match(await page.locator('#content').innerText(),/не означает универсальное покрытие/);
    await page.goto('https://ux.local/index.html',{waitUntil:'networkidle'});
    const newProjects=['ai-riksarkivet/ra-mcp','borisovodov/doru','stanford-oval/credit','fmadore/iwac-mcp-server',
      'gramps-project/gramps-web-api','scormave/gramps-web-mcp',
      'alexey-n-chernyshov/gramps-web-mcp-rs','magicianmarty/heritage-research-mcp',
      'geiserx/gramps-web-toolkit','itarunnn/jp-lit-mcp',
      'k-woitas/eperiodica-explorer','genealogy-mcp/gramps-mcp'];
    for(const repo of newProjects) {
      await page.locator('#search').fill(repo);
      assert.match(await page.locator('#shown').innerText(),/^Показано 1 из /);
      assert.match(await page.locator('.card').innerText(),/Основания · E[0-4]/);
      await page.locator('.card-links a[href^="project.html"]').click();
      await page.waitForLoadState('networkidle');
      assert.equal((await page.locator('#title').innerText()).toLowerCase(),repo);
      const details=await page.locator('#content').innerText();
      if(repo==='geiserx/gramps-web-toolkit') {
        assert.equal(details.split('Gramps Web Toolkit 0.2.10–0.2.12:').length-1,1);
        assert.equal(details.split('Gramps Web Toolkit 0.3.0:').length-1,1);
        assert.equal(details.split('Gramps Web Toolkit 1.0.0:').length-1,1);
        assert.equal(details.split('Gramps Web Toolkit 1.1.0:').length-1,1);
        assert.match(details,/ложный успех apply/);
        assert.match(details,/backup создаётся, но автоматически не восстанавливается/);
        assert.match(details,/no-op/);
        assert.match(details,/Genae/);
      }
      if(repo==='gramps-project/gramps-web-api') {
        assert.equal(details.split('Gramps Web API 3.25.1 от 31 октября:').length-1,1);
        assert.match(details,/не подтверждает обновление уже развёрнутого образа/);
        assert.match(details,/Gramps Web API 3.25.0:/);
        assert.equal(details.split('Gramps Web API 4b3a266:').length-1,1);
        assert.match(details,/не гарантия полного отсутствия утечек/);
      }
      if(repo==='itarunnn/jp-lit-mcp') {
        assert.equal(details.split('Новая карточка jp-lit-mcp 0.19.0:').length-1,1);
        assert.match(details,/1–4 OCR/);
        assert.match(details,/не независимая|не является независимой/);
      }
      // These are updates of existing cards: their latest history must be
      // visible without replacing the original research or duplicating it.
      if(repo==='scormave/gramps-web-mcp') {
        assert.equal(details.split('Scormave Gramps Web MCP: create_records в Unreleased').length-1,1);
        assert.match(details,/не проверяет дубликаты/);
        assert.equal(details.split('Scormave Gramps Web MCP: merge_objects объединяет').length-1,1);
        assert.equal(details.split('Scormave Gramps Web MCP: find_duplicates ищет').length-1,1);
        assert.equal(details.split('Scormave Gramps Web MCP 2.9.1:').length-1,1);
        assert.match(details,/сервер тот же/);
      }
      if(repo==='fmadore/iwac-mcp-server') {
        assert.equal(details.split('IWAC MCP Server 5.0.0: многословный keyword').length-1,1);
        assert.match(details,/keyword_mode=literal/);
        assert.match(details,/профиль не является контролем доступа|профиль не делает данные публичными/);
        assert.equal(details.split('IWAC MCP Server 6.0.0:').length-1,1);
        assert.match(details,/4366 статей оценены только Haiku/);
      }
      if(repo==='k-woitas/eperiodica-explorer') {
        assert.equal(details.split('Новая карточка eperiodica-explorer:').length-1,1);
        assert.match(details,/CORS-прокси/);
        assert.match(details,/SOURCE.txt/);
      }
      if(repo==='genealogy-mcp/gramps-mcp') {
        assert.equal(details.split('Новая карточка Genealogy-MCP\/gramps-mcp:').length-1,1);
        assert.equal(details.split('Genealogy-MCP\/gramps-mcp 3.15.20–3.15.23 по CHANGELOG:').length-1,1);
        assert.match(details,/GitLab/);
        assert.match(details,/не подтверждённые GitHub Releases/);
      }
      assert.match(details,/Практическое применение/);
      assert.match(details,/Практическое испытание/);
      assert.doesNotMatch(details,/Ошибка:|Сведения не установлены/);
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),repo+' research overflows');
      await page.goto('https://ux.local/digest.html',{waitUntil:'networkidle'});
      await page.locator('#q').fill(repo);
      // An existing project can have several independently reviewed events.
      assert.ok(await page.locator('article.item').count()>=1);
      if(repo==='scormave/gramps-web-mcp')assert.match(await page.locator('article.item').first().innerText(),/2\.9\.1/);
      if(repo==='fmadore/iwac-mcp-server')assert.match(await page.locator('article.item').first().innerText(),/6\.0\.0/);
      if(repo==='geiserx/gramps-web-toolkit')assert.match(await page.locator('article.item').first().innerText(),/1\.3\.0/);
      if(repo==='gramps-project/gramps-web-api')assert.match(await page.locator('article.item').first().innerText(),/4b3a266/);
      if(repo==='genealogy-mcp/gramps-mcp')assert.match(await page.locator('article.item').first().innerText(),/3\.15\.20–3\.15\.23/);
      if(repo==='itarunnn/jp-lit-mcp')assert.match(await page.locator('article.item').first().innerText(),/0\.19\.0/);
      await page.locator('article.item a[href^="project.html"]').first().click();
      await page.waitForLoadState('networkidle');
      assert.equal((await page.locator('#title').innerText()).toLowerCase(),repo);
      await page.goto('https://ux.local/tasks.html',{waitUntil:'networkidle'});
      await page.locator('#task').selectOption(repo==='stanford-oval/credit'?'research':repo==='borisovodov/doru'?'gedcom':repo==='k-woitas/eperiodica-explorer'?'transcribe':'agents');
      await page.locator('#query').fill(repo);
      assert.ok(await page.locator('#results article').count()>0);
      await page.goto('https://ux.local/index.html',{waitUntil:'networkidle'});
    }
    await page.goto('https://ux.local/project.html?repo=ai-riksarkivet%2Fhtrflow-batch',{waitUntil:'networkidle'});
    const htrDetails=await page.locator('#content').innerText();
    assert.equal(htrDetails.split('htrflow-batch: подключаемый Solr search').length-1,1);
    assert.match(htrDetails,/HTRFLOW_SOLR_URL/);
    assert.match(htrDetails,/Not for use yet/);
    await page.goto('https://ux.local/index.html',{waitUntil:'networkidle'});
    assert.ok(await page.locator('#search').evaluate(n=>n.getBoundingClientRect().top < innerHeight));
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth));
    await page.locator('#search').fill('gramps');
    const count = await page.locator('#shown').innerText();
    const url = page.url();
    assert.equal(new URL(url).searchParams.get('search'),'gramps');
    await page.locator('.card-links a').first().click();
    await page.waitForLoadState('networkidle');
    await page.goBack({waitUntil:'networkidle'});
    assert.equal(await page.locator('#search').inputValue(),'gramps');
    assert.equal(await page.locator('#shown').innerText(),count);
    await page.reload({waitUntil:'networkidle'});
    assert.equal(await page.locator('#shown').innerText(),count);
    await page.locator('#reset-catalog').click();
    assert.equal(await page.locator('#search').inputValue(),'');
    assert.equal(new URL(page.url()).search,'');
    await page.goto('https://ux.local/tasks.html',{waitUntil:'networkidle'});
    await page.locator('#task').selectOption({index:1});
    await page.locator('#query').fill('несуществующийтест123');
    await page.reload({waitUntil:'networkidle'});
    assert.equal(await page.locator('#query').inputValue(),'несуществующийтест123');
    assert.match(await page.locator('#results').innerText(),/Нет совпадений/);
    await page.locator('#reset-tasks').click();
    assert.equal(await page.locator('#task').inputValue(),'');
    assert.equal(await page.locator('#query').inputValue(),'');
    await page.locator('#task').selectOption('transcribe');
    const dataCard=page.locator('.task-group').filter({has:page.getByRole('heading',{name:/^Наборы данных и примеры/})});
    assert.match(await dataCard.innerText(),/abbyy\/jfk-ocr/);
    await page.locator('#role').selectOption('data');
    assert.ok(await page.locator('#results article').count()>=1);
    assert.equal(await page.locator('#results .task-group').count(),1);
    await page.locator('#role').selectOption('');
    const buttons=page.locator('#results [data-compare]');
    for(let i=0;i<3;i++)await buttons.nth(i).click();
    assert.equal(await page.locator('.comparison-card').count(),3);
    await buttons.nth(3).click();
    assert.equal(await page.locator('.comparison-card').count(),3);
    assert.match(await page.locator('#compare-message').innerText(),/не больше трёх/);
    await page.locator('#query').fill('no-match-123');
    assert.equal(await page.locator('.comparison-card').count(),3);
    await page.locator('.comparison-card button').first().click();
    assert.equal(await page.locator('.comparison-card').count(),2);
    await page.locator('#clear-comparison').click();
    assert.equal(await page.locator('.comparison-card').count(),0);
    await page.goto('https://ux.local/project.html?repo=gramps-project%2Fgramps-web',{waitUntil:'networkidle'});
    const titles=await page.locator('#content > section > h2').allTextContents();
    assert.deepEqual(titles.slice(0,3),['Назначение','Практическое применение','Ограничения и редакционная оценка']);
    assert.equal(await page.locator('details').filter({has:page.locator('summary').filter({hasText:'Из путеводителя'})}).count(),1);
    for (const width of [375,1440]) {
      await page.setViewportSize({width,height:900});
      let expected;
      for (const name of ['index','digest','tasks','licenses','priorities','project']) {
        await page.goto('https://ux.local/'+name+'.html',{waitUntil:'networkidle'});
        const bounds = await page.locator('.site-nav a').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect();return [r.x,r.y,r.width,r.height]}));
        if(expected) assert.deepEqual(bounds,expected);
        expected=bounds;
        assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth <= innerWidth));
        assert.equal(await page.locator('.skip-link').count(),1);
      }
    }
    assert.deepEqual(runtimeErrors,[]);
    await page.goto('https://ux.local/priorities.html?priority=P1',{waitUntil:'networkidle'});
    const priorityAudit=JSON.parse(await fs.readFile(path.join(root,'priority-review.json'),'utf8'));
    assert.equal(await page.locator('#priority').inputValue(),'P1');
    assert.equal(await page.locator('#items article').count(),priorityAudit.counts.priorities.P1);
    assert.ok((await page.locator('#priority-metrics').innerText()).includes(priorityAudit.counts.p1_e0+' меток P1 с E0'));
    await page.locator('#reset-priorities').click();
    await page.locator('#assessment').selectOption('missing');
    assert.equal(await page.locator('#items article').count(),priorityAudit.counts.states.missing);
    await page.locator('#reset-priorities').click();
    await page.locator('#task').selectOption('agents');
    await page.locator('#q').fill('scormave/gramps-web-mcp');
    assert.equal(await page.locator('#items article').count(),1);
    assert.ok((await page.locator('#items').innerText()).includes(priorityAudit.projects.find(x=>x.project==='scormave/gramps-web-mcp').state_label));
    const proposal=page.locator('.practical-proposal');
    assert.equal(await proposal.count(),1);
    assert.match(await proposal.innerText(),/P2.*утверждено пользователем/);
    assert.match(await proposal.innerText(),/read-only/);
    assert.equal(await proposal.locator('a').count(),2);
    await page.reload({waitUntil:'networkidle'});
    assert.equal(await page.locator('#q').inputValue(),'scormave/gramps-web-mcp');
    await page.locator('#reset-priorities').click();
    await page.locator('#assessment').selectOption('reference_issue');
    assert.equal(await page.locator('#items article').count(),priorityAudit.counts.states.reference_issue);
    assert.match(await page.locator('#items').innerText(),/HTTP 404/);
    await page.locator('#reset-priorities').click();
    await page.locator('#proposed-priority').selectOption('P1');
    assert.equal(await page.locator('#items article').count(),priorityAudit.projects.filter(x=>x.practical_proposal?.proposed_priority==='P1').length);
    await page.reload({waitUntil:'networkidle'});
    assert.equal(await page.locator('#proposed-priority').inputValue(),'P1');
    await page.locator('#reset-priorities').click();
    await page.locator('#q').fill('Бразилия');
    assert.equal(await page.locator('#items article').count(),1);
    assert.match(await page.locator('#items').innerText(),/Desembarque/);
    await page.locator('#reset-priorities').click();
    await page.locator('#proposed-priority').selectOption('Не оценён');
    await page.locator('#q').fill('w3c/prov');
    assert.match(await page.locator('.practical-proposal').innerText(),/E0.*триаж/);
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
    assert.deepEqual(runtimeErrors,[]);
    console.log('Browser UX regression passed: twelve watch projects (search, research, digest links, task matching), htrflow Solr history; back/reload, URL filters, reset, mobile search, 12 navigation layouts; no console/page errors.');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1});
