"""遠距餵食回歸、日夜混合問答及天空物件完整生命週期。"""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for width,height in [(390,844),(844,390),(1280,850)]:
  page=b.new_page(viewport={'width':width,'height':height},has_touch=True);errors=[];requests=[]
  page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
  page.route('https://savanna-sky.test/',lambda r:r.fulfill(body=(ROOT/'index.html').read_bytes(),content_type='text/html'));page.goto('https://savanna-sky.test/')
  page.evaluate("()=>{window.spoken=[];speechSynthesis.speak=u=>spoken.push(u.text);speechSynthesis.cancel=()=>{};window.actualChance=skyQuestionAvailable;let seed=4;Math.random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;}}")
  # The original failing mobile distance/65-second lifetime: use a real food quiz and placement.
  page.evaluate("worldTime=30;animals=[makeAnimal('elephant',100,grassTop(100)+20)];animals[0].lifeLeft=65;animals[0].nextEat=999;animals[0].nextDrink=0;animals[0].nextRest=0;foodBag=[VEGETABLES.find(f=>f.id==='carrot')];foods=[]")
  page.locator('#food').click();page.locator('.option[data-id="carrot"]').click();page.locator('#confirm').click()
  box=page.locator('#scene').bounding_box();page.locator('#scene').tap(position={'x':box['width']*.5,'y':box['height']*.9})
  assert page.evaluate("animals[0].mode==='toFood'"),page.evaluate('({a:animals[0],foods,pending,H})')
  result=page.evaluate("""()=>{const portions=[],eater=animals[0];let last=5;for(let i=0;i<800;i++){update(.05);const n=foods[0]?.bites||0;if(n!==last){portions.push(n);last=n;}}return {portions,empty:foods.length===0,alive:animals.includes(eater)};}""")
  assert result=={'portions':[4,3,2,1,0],'empty':True,'alive':True},result
  # A food beside the enlarged pond has a dry approach, and predators do not eat vegetables.
  assert page.evaluate("""()=>{worldTime=60;animals=[makeAnimal('elephant',450,groundY(H*.7))];animals[0].lifeLeft=120;foods=[makeFood('carrot',pond().x-pond().rx-20,pond().y)];inviteToFood(foods[0]);const dry=onGrass(animals[0].targetX,animals[0].targetY);for(let i=0;i<800;i++)update(.05);return dry&&foods.length===0;}""")
  assert page.evaluate("()=>{animals=[makeAnimal('lion',200,groundY(H*.7))];foods=[makeFood('carrot',300,groundY(H*.7))];inviteToFood(foods[0]);worldTime=60;for(let i=0;i<400;i++)update(.05);return foods[0].bites===5;}")
  # Daytime aircraft share the 26-entry deck; night retains approximately 25% sky questions.
  result=page.evaluate("""()=>{animals=[];foods=[];skyItems=[];skyQuestionAvailable=actualChance;quizKind='animal';const results=[];
   for(const [world,ids]of [[60,['airplane','helicopter']],[210,['star','meteor']]]){worldTime=world;let specials=0,bad=false;const seen=new Set();for(let i=0;i<500;i++){pickQuestion();if(skyDef(question.id)){specials++;seen.add(question.id);if(!ids.includes(question.id))bad=true;}}results.push({specials,bad,seen:seen.size});}return results;}""")
  assert 36<=result[0]['specials']<=40 and 85<result[1]['specials']<170 and all(not r['bad'] and r['seen']==2 for r in result),result
  # Observe ten full daytime cycles: every one of the 26 types must appear exactly ten times.
  assert page.evaluate("""()=>{worldTime=60;animals=[];skyItems=[];bag=[];previous=null;quizKind='animal';skyQuestionAvailable=actualChance;const counts={};for(let i=0;i<260;i++){pickQuestion();counts[question.id]=(counts[question.id]||0)+1;}return Object.keys(counts).length===26&&Object.values(counts).every(n=>n===10)&&counts.airplane===10&&counts.helicopter===10;}""")
  # Four real quiz/voice/confirm/place flows; sky rejects ground placement.
  for id,world,other in [('star',210,'meteor'),('meteor',210,'star'),('airplane',60,'helicopter'),('helicopter',60,'airplane')]:
   page.evaluate("([world,other])=>{animals=[];foods=[];skyItems=[];worldTime=world;skyQuestionAvailable=()=>true;previous=other;if(!nightQuiz())bag=[skyDef(other==='airplane'?'helicopter':'airplane')];}",[world,other])
   page.locator('#add').click();assert page.evaluate('question.id')==id
   opts=page.locator('.option').evaluate_all('(els)=>els.map(e=>e.dataset.id)');assert len(set(opts))==4 and id in opts
   assert page.evaluate("[...$('options').children].every(b=>!skyDef(b.dataset.id)||eligibleSkyWords().some(s=>s.id===b.dataset.id))")
   page.locator(f'.option[data-id="{id}"]').click();assert page.evaluate('spoken.at(-1)')==id
   page.locator('#confirm').click();assert page.evaluate("pending.kind==='sky'")
   page.locator('#scene').tap(position={'x':box['width']*.2,'y':box['height']*.7});assert page.evaluate('pending!==null&&skyItems.length===0')
   page.locator('#scene').tap(position={'x':box['width']*.45,'y':box['height']*.2});assert page.evaluate('pending===null&&skyItems.length===1&&animals.length===0')
   if id=='star':
    page.locator('#scene').tap(position={'x':box['width']*.45,'y':box['height']*.2});assert page.locator('#entity-word').inner_text()=='star'
   elif id=='meteor':
    assert page.evaluate("()=>{const a=skyItems[0],x=a.x;update(.1);const moved=a.x!==x;for(let i=0;i<65;i++)update(.05);return moved&&skyItems.length===0;}")
  # Stars persist for the night and disappear at dawn; no reset on reopening.
  page.evaluate("worldTime=210;skyItems=[makeSkyItem('star',500,H*.2)];save()")
  page.reload();assert page.evaluate("skyItems.length===1&&skyItems[0].id==='star'")
  assert page.evaluate("()=>{worldTime=230;update(.1);const still=skyItems.length===1;worldTime=20;update(.1);return still&&skyItems.length===0;}")
  # Each aircraft makes exactly 2 or 4 traversals, then flies completely off-screen.
  for id in ['airplane','helicopter']:
   for trips in [1,2]:
    result=page.evaluate("""([id,trips])=>{worldTime=40;const a=makeSkyItem(id,200,H*.2);a.dir=1;a.roundTrips=trips;a.passesLeft=trips*2;skyItems=[a];let previous=a.passesLeft;const passes=[];let exited=false;
     for(let i=0;i<2000&&skyItems.length;i++){update(.05);if(a.passesLeft!==previous){passes.push(a.passesLeft);previous=a.passesLeft;}if(a.state==='exiting')exited=true;}
     return {passes,exited,gone:skyItems.length===0};}""",[id,trips])
    assert result=={'passes':list(range(trips*2-1,-1,-1)),'exited':True,'gone':True},(id,trips,result)
  page.evaluate("worldTime=60;skyItems=[makeSkyItem('airplane',500,H*.2)];skyItems[0].roundTrips=2;skyItems[0].passesLeft=2;skyItems[0].dir=-1;skyItems[0].age=15;save()")
  page.reload();assert page.evaluate('skyItems[0].passesLeft===2&&skyItems[0].roundTrips===2&&skyItems[0].dir===-1')
  # Quiz and hidden-page update gate keep flight clocks stationary; size changes keep sky positions.
  page.locator('#add').click();before=page.evaluate('JSON.stringify(skyItems)');page.evaluate('update(5)');assert before==page.evaluate('JSON.stringify(skyItems)');page.locator('#close').click()
  page.set_viewport_size({'width':height,'height':width});page.wait_for_timeout(80);assert page.evaluate('skyItems.every(a=>a.y>=0&&a.y<H)')
  # Sky capacity forces normal animal questions, animal capacity still permits sky questions.
  assert page.evaluate("()=>{worldTime=60;animals=[];skyItems=Array.from({length:MAX_SKY},()=>makeSkyItem('airplane',500,H*.2));quizKind='animal';let ok=true;for(let i=0;i<40;i++){pickQuestion();if(skyDef(question.id))ok=false;}skyItems=[];animals=Array.from({length:MAX_ANIMALS},()=>makeAnimal('lion',100,groundY(H*.7)));pickQuestion();return ok&&!!skyDef(question.id);}")
  assert not errors,errors
  assert all(u=='https://savanna-sky.test/' for u in requests),requests
  print(f'PASS {width}×{height} 遠距五口餵食／池邊乾路／肉食限制／日夜機率與四種問答發音部署／星星晨消、流星離場／1、2 趟飛行、保存及暫停／容量限制')
  page.close()
 b.close()
