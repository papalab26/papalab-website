"""插畫比例、個別作息、打招呼及定時離場的實際瀏覽器測試。"""
from pathlib import Path
from io import BytesIO
from PIL import Image
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for width,height in [(390,844),(844,390),(1280,850)]:
  page=b.new_page(viewport={'width':width,'height':height});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.route('https://savanna-life.test/',lambda r:r.fulfill(body=(ROOT/'index.html').read_bytes(),content_type='text/html'));page.goto('https://savanna-life.test/')
  page.evaluate('skyQuestionAvailable=()=>false;speechSynthesis.speak=()=>{};speechSynthesis.cancel=()=>{}')
  page.locator('#add').click()
  # A real screenshot: a circular test mark must remain circular after CSS layout.
  page.evaluate("()=>{const c=$('animal-picture').getContext('2d');c.clearRect(0,0,400,230);c.fillStyle='#000';c.beginPath();c.arc(200,120,40,0,Math.PI*2);c.fill();}")
  img=Image.open(BytesIO(page.locator('#animal-picture').screenshot())).convert('RGB')
  pts=[(x,y)for y in range(40,img.height)for x in range(img.width//4,img.width*3//4)if max(img.getpixel((x,y)))<35]
  assert pts
  dx=max(x for x,y in pts)-min(x for x,y in pts)+1;dy=max(y for x,y in pts)-min(y for x,y in pts)+1
  assert abs(dx/dy-1)<.06,(width,dx,dy)
  page.locator('#close').click()
  result=page.evaluate("""()=>{
   animals=Array.from({length:100},()=>makeAnimal('lion',200,groundY(H*.7)));
   return {valid:animals.every(a=>a.lifeLeft>=60&&a.lifeLeft<=120&&a.sleepAt>=190&&a.sleepAt<=220&&a.wakeAt>=3&&a.wakeAt<=24),sleepSpread:new Set(animals.map(a=>Math.round(a.sleepAt))).size,wakeSpread:new Set(animals.map(a=>Math.round(a.wakeAt))).size};
  }""")
  assert result['valid'] and result['sleepSpread']>10 and result['wakeSpread']>10,result
  # Controlled different schedules: one asleep while the other is awake, and different dawn times.
  result=page.evaluate("""()=>{
   animals=[makeAnimal('lion',200,groundY(H*.7)),makeAnimal('zebra',600,groundY(H*.7))];
   for(const [i,a]of animals.entries()){a.lifeLeft=999;a.sleepAt=i?218:195;a.wakeAt=i?22:4;a.nextRest=a.nextDrink=a.nextEat=a.nextSocial=999;a.wait=999;}
   worldTime=200;update(.01);const evening=animals.map(a=>a.mode);
   worldTime=230;update(.01);worldTime=10;update(.01);const dawn=animals.map(a=>a.mode);
   worldTime=25;update(.01);return {evening,dawn,awake:animals.every(a=>a.mode!=='sleeping')};
  }""")
  assert result=={'evening':['sleeping','wander'],'dawn':['wander','sleeping'],'awake':True},result
  # Nearby animals greet facing each other, then release both references safely.
  result=page.evaluate("""()=>{
   worldTime=60;animals=[makeAnimal('lion',200,groundY(H*.7)),makeAnimal('zebra',330,groundY(H*.7))];
   for(const a of animals){a.lifeLeft=999;a.nextRest=a.nextEat=a.nextDrink=999;a.nextSocial=0;a.wait=999;}
   greet(animals[0]);update(.05);const greeted=animals.every(a=>a.mode==='greeting'&&a.partner)&&animals[0].dir===1&&animals[1].dir===-1;render();
   const c=$('animal-picture').getContext('2d');c.clearRect(0,0,400,230);drawAnimal(c,'lion',200,205,140,1,0,0,false);const before=$('animal-picture').toDataURL();c.clearRect(0,0,400,230);drawAnimal(c,'lion',200,205,140,1,0,.8,false,'greeting');const different=before!==$('animal-picture').toDataURL();
   for(let i=0;i<100;i++)update(.05);return {greeted,different,released:animals.every(a=>a.mode!=='greeting'&&a.partner===null)};
  }""")
  assert all(result.values()),result
  # Every species starts leaving at its deadline, moves visibly and is removed, including sleepers.
  # Allow the existing route planner one frame to discard an already-reached waypoint.
  result=page.evaluate("""()=>{
   worldTime=230;animals=ANIMALS.map((d,i)=>{const a=fitHabitat(makeAnimal(d.id,habitat(d.id)==='water'||habitat(d.id)==='shore'?pond().x:200,habitat(d.id)==='water'||habitat(d.id)==='shore'?pond().y:groundY(H*.7)));a.lifeLeft=1;a.nextSocial=a.nextRest=a.nextDrink=a.nextEat=999;return a;});update(.05);
   for(let i=0;i<18;i++)update(.05);const notEarly=animals.length===24&&animals.every(a=>a.mode!=='leaving');update(.06);
   const departures=animals.every(a=>a.mode==='leaving');const x=animals[0].x,y=animals[0].y;for(let i=0;i<3;i++)update(.05);const moved=animals[0].x!==x||animals[0].y!==y;
   for(let i=0;i<700;i++)update(.05);return {notEarly,departures,moved,empty:animals.length===0,count:$('count').textContent,species:$('species').textContent,saved:JSON.parse(localStorage.getItem(STORE)).animals.length};
  }""")
  assert result=={'notEarly':True,'departures':True,'moved':True,'empty':True,'count':'0','species':'0','saved':0},result
  # Actual randomized 60–120 second deadlines, without extending lifetime for this test.
  assert page.evaluate("""()=>{
   worldTime=30;animals=ANIMALS.map((d,i)=>fitHabitat(makeAnimal(d.id,habitat(d.id)==='water'||habitat(d.id)==='shore'?pond().x:100+i*35,habitat(d.id)==='water'||habitat(d.id)==='shore'?pond().y:groundY(H*.7))));
   const records=animals.map(a=>({a,deadline:a.lifeLeft,leftAt:null}));
   for(let step=1;step<=3400;step++){update(.05);for(const r of records){if(r.a.mode==='leaving'&&r.leftAt===null)r.leftAt=step*.05;}}
   return records.every(r=>r.leftAt>=60&&r.leftAt<=120.05&&Math.abs(r.deadline-r.leftAt)<.06)&&animals.length===0;
  }""")
  # Quiz overlay pauses departure clocks; remaining time and schedules survive save/restore.
  page.evaluate("animals=[makeAnimal('elephant',200,groundY(H*.7))];animals[0].lifeLeft=42;animals[0].sleepAt=202;animals[0].wakeAt=14;worldTime=60;save()")
  page.reload();assert page.evaluate('animals.length===1&&animals[0].lifeLeft>41&&animals[0].sleepAt===202&&animals[0].wakeAt===14')
  page.locator('#add').click();before=page.evaluate('animals[0].lifeLeft');page.evaluate('update(30)');assert page.evaluate('animals[0].lifeLeft')==before
  page.locator('#close').click()
  assert not errors,errors
  print(f'PASS {width}×{height} 插畫圓形像素比例／個別睡醒／互動與清理／24 種離場及計數存檔／答題暫停與恢復')
  page.close()
 b.close()
