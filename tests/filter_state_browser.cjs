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
    const root = path.resolve(__dirname,'../docs');
    await page.route('https://ux.local/**', async route => {
      const name = path.basename(new URL(route.request().url()).pathname) || 'index.html';
      const type = name.endsWith('.js') ? 'application/javascript' : name.endsWith('.css') ? 'text/css' : name.endsWith('.json') ? 'application/json' : 'text/html';
      await route.fulfill({body:await fs.readFile(path.join(root,name)),contentType:type});
    });
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
    const dataCard=page.locator('.task-group').filter({has:page.getByRole('heading',{name:'Наборы данных и примеры (1)',exact:true})});
    assert.match(await dataCard.innerText(),/abbyy\/jfk-ocr/);
    await page.locator('#role').selectOption('data');
    assert.equal(await page.locator('#results article').count(),1);
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
    console.log('Browser UX regression passed: back/reload, URL filters, reset, mobile search, 12 navigation layouts.');
  } finally { await browser.close(); }
})().catch(error=>{console.error(error);process.exitCode=1});
