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
    const newProjects=['ai-riksarkivet/ra-mcp','borisovodov/doru','stanford-oval/credit','fmadore/iwac-mcp-server',
      'gramps-project/gramps-web-api','scormave/gramps-web-mcp',
      'alexey-n-chernyshov/gramps-web-mcp-rs','magicianmarty/heritage-research-mcp',
      'geiserx/gramps-web-toolkit','itarunnn/jp-lit-mcp'];
    for(const repo of newProjects) {
      await page.locator('#search').fill(repo);
      assert.match(await page.locator('#shown').innerText(),/^Показано 1 из /);
      const existingLegacy=repo==='scormave/gramps-web-mcp';
      assert.match(await page.locator('.card').innerText(),existingLegacy?/Тестирование не указано/:/Не тестировался независимо/);
      await page.locator('.card-links a[href^="project.html"]').click();
      await page.waitForLoadState('networkidle');
      assert.equal((await page.locator('#title').innerText()).toLowerCase(),repo);
      const details=await page.locator('#content').innerText();
      if(repo==='geiserx/gramps-web-toolkit') {
        assert.equal(details.split('Gramps Web Toolkit 0.2.10–0.2.12:').length-1,1);
        assert.match(details,/no-op/);
        assert.match(details,/Genae/);
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
      }
      if(repo==='fmadore/iwac-mcp-server') {
        assert.equal(details.split('IWAC MCP Server 5.0.0: многословный keyword').length-1,1);
        assert.match(details,/keyword_mode=literal/);
        assert.match(details,/профиль не является контролем доступа|профиль не делает данные публичными/);
      }
      assert.match(details,/Практическое применение/);
      assert.match(details,existingLegacy?/Независимое тестирование: Не подтверждено/:/Независимое тестирование: Не тестировалось/);
      assert.doesNotMatch(details,/Ошибка:|Сведения не установлены/);
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),repo+' research overflows');
      await page.goto('https://ux.local/digest.html',{waitUntil:'networkidle'});
      await page.locator('#q').fill(repo);
      // An existing project can have several independently reviewed events.
      assert.ok(await page.locator('article.item').count()>=1);
      if(repo==='scormave/gramps-web-mcp')assert.match(await page.locator('article.item').first().innerText(),/create_records в Unreleased/);
      if(repo==='fmadore/iwac-mcp-server')assert.match(await page.locator('article.item').first().innerText(),/5\.0\.0: многословный keyword/);
      if(repo==='geiserx/gramps-web-toolkit')assert.match(await page.locator('article.item').first().innerText(),/0\.2\.10–0\.2\.12/);
      if(repo==='itarunnn/jp-lit-mcp')assert.match(await page.locator('article.item').first().innerText(),/0\.19\.0/);
      await page.locator('article.item a[href^="project.html"]').first().click();
      await page.waitForLoadState('networkidle');
      assert.equal((await page.locator('#title').innerText()).toLowerCase(),repo);
      await page.goto('https://ux.local/tasks.html',{waitUntil:'networkidle'});
      await page.locator('#task').selectOption(repo==='stanford-oval/credit'?'research':repo==='borisovodov/doru'?'gedcom':'agents');
      await page.locator('#query').fill(repo);
      assert.ok(await page.locator('#results article').count()>0);
      await page.goto('https://ux.local/index.html',{waitUntil:'networkidle'});
    }
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
    console.log('Browser UX regression passed: ten watch projects (search, research, digest links, task matching); back/reload, URL filters, reset, mobile search, 12 navigation layouts; no console/page errors.');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1});
