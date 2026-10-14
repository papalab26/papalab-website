from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=b.new_page(viewport={'width':390,'height':844});errors=[];requests=[]
 page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
 page.set_content((ROOT/'index.html').read_text())
 # Every food still has four valid choices and removes exactly five portions.
 page.evaluate("skyQuestionAvailable=()=>false;speechSynthesis.speak=()=>{};speechSynthesis.cancel=()=>{};const originalMake=makeAnimal;makeAnimal=(...args)=>({...originalMake(...args),lifeLeft:9999,nextSocial:9999})")
 for i in range(6):
  page.locator('#food').click();q=page.evaluate('question.id');opts=page.locator('.option').evaluate_all('(els)=>els.map(e=>e.dataset.id)')
  assert len(set(opts))==4 and q in opts
  page.locator(f'.option[data-id="{q}"]').click();page.locator('#confirm').click()
  area=page.locator('#scene').bounding_box();page.locator('#scene').click(position={'x':area['width']*.23,'y':area['height']*.78})
  assert page.evaluate('foods.length')==i+1
 result=page.evaluate("""()=>{
  worldTime=60;foods=[makeFood('carrot',300,groundY(H*.65))];animals=[makeAnimal('elephant',200,groundY(H*.65))];const a=animals[0];a.nextEat=0;a.nextDrink=9999;a.nextRest=9999;let bites=[];let last=5;for(let i=0;i<3000&&foods.length;i++){update(.05);const n=foods[0]?foods[0].bites:0;if(n!==last){bites.push(n);last=n}}return bites;
 }""")
 assert result==[4,3,2,1,0],result
 # A dry-land animal routes around the pond instead of crossing its centre.
 report=page.evaluate("""()=>{
  const p=pond();worldTime=50;animals=[makeAnimal('lion',p.x-p.rx-60,p.y)];const a=animals[0];a.targetX=W-70;a.targetY=p.y-p.ry-55;a.nextDrink=a.nextEat=a.nextRest=9999;let entered=false,reached=false;
  for(let i=0;i<4000;i++){update(.05);if(inPond(a.x,a.y))entered=true;if(Math.hypot(a.x-a.targetX,a.y-a.targetY)<5){reached=true;break}}return {entered,reached,x:a.x};
 }""")
 assert not report['entered'] and report['reached'],report
 # Old food positions inside the enlarged pond migrate onto dry grass, without losing portions.
 page.evaluate("foods=[makeFood('corn',pond().x,pond().y,2)];fitFood(foods[0]);save()")
 assert page.evaluate('!inPond(foods[0].x,foods[0].y)&&foods[0].bites===2')
 storage_page=b.new_page();storage_page.on('pageerror',lambda e:errors.append(str(e)));storage_page.route('https://savanna-save.test/',lambda r:r.fulfill(body=(ROOT/'index.html').read_bytes(),content_type='text/html'));storage_page.goto('https://savanna-save.test/')
 legacy=storage_page.evaluate("()=>{const old=JSON.stringify({version:2,worldTime:60,animals:[{id:'elephant',x:.2,y:.5}],foods:[]});localStorage.removeItem(STORE);localStorage.setItem(LEGACY_STORE,old);animals=[];foods=[];restore();save();return animals.length===1&&animals[0].id==='elephant'&&localStorage.getItem(LEGACY_STORE)===old}")
 assert legacy
 storage_page.close()
 # Tiny portrait and landscape keep controls on-screen, and the enlarged pond may extend past the lower right edge.
 for width,height in [(320,568),(844,390)]:
  page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(70)
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  for selector in ['#add','#food','#scene']:
   rect=page.locator(selector).bounding_box();assert rect and rect['y']+rect['height']<=height+1,(selector,rect,height)
  assert page.evaluate('pond().x+pond().rx>W && pond().y+pond().ry>H')
 assert not errors,errors
 assert not requests,requests
 print('PASS 六種食物問答與五次份量、陸地動物繞池塘、舊食物位置轉換、320px 直向／橫向及單檔無外部請求／JS 錯誤。')
 b.close()
