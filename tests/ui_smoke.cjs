/* Execute shipped renderers against real data with a minimal document fixture. */
const fs = require('node:fs'), path = require('node:path'), vm = require('node:vm'), assert = require('node:assert/strict');
const root = process.argv[2] ? path.resolve(process.argv[2]) : path.resolve(__dirname, '..');
const read = name => fs.readFileSync(path.join(root, name), 'utf8');
const catalog = JSON.parse(read('catalog.json')), research = JSON.parse(read('docs/research.json')), digest = JSON.parse(read('digest.json'));
function fixture(seed) {
  const elements = new Map();
  const get = id => { if (!elements.has(id)) elements.set(id, {value:'', innerHTML:'', textContent:'', addEventListener(){}}); return elements.get(id); };
  get('seed').textContent = JSON.stringify(seed);
  const context = vm.createContext({document:{getElementById:get, title:''}, URL, URLSearchParams, structuredClone,
    location:{search:''}, localStorage:{getItem(){throw Error('Storage must never override published data');},setItem(){throw Error('No persistence');}}, console});
  vm.runInContext(read('docs/watch-ui.js'), context);
  return {get,context};
}
function count(html, className) { return (html.match(new RegExp('<article class="' + className, 'g')) || []).length; }
(async () => {
  const page = fixture(catalog), html = read('docs/index.html');
  const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
  assert.equal(scripts.length, 1);
  vm.runInContext(scripts[0][1], page.context);
  assert.equal(count(page.get('cards').innerHTML, 'card'), catalog.length);
  for (const rating of ['Высокий','Специализированный / зависит от задачи','Не оценено']) {
    const expected = catalog.filter(x => (x.russia_applicability?.rating || 'Не оценено') === rating).length;
    page.get('russia').value = rating;
    vm.runInContext('render()', page.context);
    assert.equal(count(page.get('cards').innerHTML,'card'), expected);
  }
  page.get('russia').value=''; page.get('search').value='NO_SUCH_PROJECT_12345';
  vm.runInContext('render()', page.context);
  assert.equal(count(page.get('cards').innerHTML,'card'),0);
  page.get('search').value=''; page.get('priority').value='P1'; page.get('russia').value='Высокий';
  vm.runInContext('render()', page.context);
  assert.equal(count(page.get('cards').innerHTML,'card'), catalog.filter(x => x.priority==='P1' && x.russia_applicability.rating==='Высокий').length);
  const dg = fixture(digest);
  vm.runInContext(read('docs/digest-ui.js'), dg.context);
  const eventCount = digest.reduce((n,d) => n+d.items.length, 0);
  assert.equal(count(dg.get('content').innerHTML,'item'),eventCount);
  assert.equal((dg.get('content').innerHTML.match(/project.html\?repo=/g)||[]).length,eventCount);
  for (const day of digest) for (const item of day.items) assert.ok(catalog.some(x =>
    x.name.toLowerCase() === item.repo.toLowerCase() || x.url.toLowerCase().replace(/\/$/,'').replace('https://github.com/','') === item.repo.toLowerCase()), 'Digest project lookup: ' + item.repo);
  dg.get('q').value='NO_SUCH_EVENT'; dg.get('q').oninput();
  assert.equal(count(dg.get('content').innerHTML,'item'),0);
  for (const name of [catalog[0].name, catalog.find(x => !research[x.name.toLowerCase()]).name]) {
    const pr = fixture(null);
    pr.context.location.search = '?repo=' + encodeURIComponent(name);
    pr.context.fetch = async url => ({ok:true, json:async()=>({'catalog.json':catalog,'research.json':research,'digest.json':digest}[url])});
    await vm.runInContext(read('docs/project-ui.js'), pr.context);
    assert.equal(pr.get('title').textContent,name);
    assert.match(pr.get('content').innerHTML,/Доступность сервиса из РФ/);
    const r=research[name.toLowerCase()];
    if (r?.guide_excerpt) assert.ok(pr.get('content').innerHTML.includes(pr.context.WatchUI.esc(r.guide_excerpt)));
  }
  const missing=fixture(null); missing.context.location.search='?repo=missing';
  missing.context.fetch=async url=>({ok:true,json:async()=>({'catalog.json':catalog,'research.json':research,'digest.json':digest}[url])});
  await vm.runInContext(read('docs/project-ui.js'),missing.context);
  assert.match(missing.get('content').textContent,/Проект не найден/);
  for (const [key,r] of Object.entries(research)) if (r.watch_events?.length) {
    const pr=fixture(null); pr.context.location.search='?repo='+encodeURIComponent(key);
    pr.context.fetch=async url=>({ok:true,json:async()=>({'catalog.json':catalog,'research.json':research,'digest.json':digest}[url])});
    await vm.runInContext(read('docs/project-ui.js'),pr.context);
    for (const event of r.watch_events) {
      assert.equal(pr.get('content').innerHTML.split(pr.context.WatchUI.esc(event.change)).length-1,1,'Event must render once across research/history/digest');
      if (event.claims_vs_verified) assert.match(pr.get('content').innerHTML,/Заявления и проверка/);
      if (event.claims_vs_verified?.verified) assert.match(pr.get('content').innerHTML,/Проверено по источнику/);
      if (event.claims_vs_verified?.author_claims) assert.match(pr.get('content').innerHTML,/Заявления авторов/);
    }
  }
  assert.equal(page.context.WatchUI.url('javascript:alert(1)'), '');
  console.log(`UI smoke passed: ${catalog.length} cards; source-backed Russia filters; combined/empty filters; ${eventCount} events and research links; full/missing research; no storage; unsafe URL rejected.`);
})().catch(error => {console.error(error);process.exitCode=1;});
