"""八種夜行動物的問答／造型／活動與日夜題庫切換驗證。"""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for width,height in [(390,844),(844,390),(1280,850)]:
  page=b.new_page(viewport={'width':width,'height':height},has_touch=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.route('https://savanna-night.test/',lambda r:r.fulfill(body=(ROOT/'index.html').read_bytes(),content_type='text/html'));page.goto('https://savanna-night.test/')
  page.evaluate("window.spoken=[];speechSynthesis.speak=u=>spoken.push(u.text);speechSynthesis.cancel=()=>{};window.actualChance=skyQuestionAvailable;skyQuestionAvailable=()=>false;worldTime=200")
  assert page.evaluate('NOCTURNAL_ANIMALS.length===8&&ANIMALS.length===24&&ALL_ANIMALS.length===32')
  assert page.evaluate('NOCTURNAL_ANIMALS.map(a=>a.id)')==['owl','bat','fox','hedgehog','raccoon','mouse','porcupine','bushbaby']
  assert page.locator('#species-total').inner_text()=='32'
  seen=[]
  # Real questions have only nocturnal creatures + star/meteor as distractors.
  for i in range(8):
   page.locator('#add').click();q=page.evaluate('question.id');seen.append(q)
   opts=page.locator('.option').evaluate_all('(els)=>els.map(e=>e.dataset.id)');assert len(set(opts))==4 and q in opts
   assert page.evaluate("[...$('options').children].every(b=>NOCTURNAL_ANIMALS.some(a=>a.id===b.dataset.id)||['star','meteor'].includes(b.dataset.id))")
   page.locator(f'.option[data-id="{q}"]').click();assert page.evaluate('spoken.at(-1)===question.word')
   page.locator('#confirm').click();box=page.locator('#scene').bounding_box();page.locator('#scene').tap(position={'x':box['width']*.20,'y':box['height']*.66})
   assert page.evaluate('pending===null&&animals.length==='+str(i+1))
   assert page.evaluate('animals.at(-1).mode!=="sleeping"')
  assert len(set(seen))==8
  # Both sides of a day/night switch filter all four options, including leftover decks.
  result=page.evaluate("""()=>{
   skyQuestionAvailable=actualChance;const reports=[];
   for(const world of [60,210,20,220,170,175,5,8]){worldTime=world;quizKind='animal';let bad=false,sky=0;const seen=new Set();
    for(let i=0;i<100;i++){nextQuestion();const allowed=[...eligibleAnimals(),...eligibleSkyWords()].map(d=>d.id);if(!allowed.includes(question.id)||[...$('options').children].some(b=>!allowed.includes(b.dataset.id)))bad=true;if(skyDef(question.id))sky++;else seen.add(question.id);}
    reports.push({world,bad,sky,kinds:seen.size,expected:eligibleAnimals().length});}
   return reports;
  }""")
  assert all(not r['bad'] and (6<=r['sky']<=10 if r['expected']==24 else 8<r['sky']<45) and r['kinds']==r['expected'] for r in result),result
  # Independent shuffled night deck cannot repeat consecutive questions, and each 8-question cycle covers all species.
  assert page.evaluate("""()=>{worldTime=210;quizKind='animal';skyQuestionAvailable=()=>false;nightBag=[];previous=null;let last=null;for(let round=0;round<4;round++){const ids=new Set();for(let i=0;i<8;i++){pickQuestion();if(question.id===last)return false;ids.add(question.id);last=question.id;}if(ids.size!==8)return false;}return true;}""")
  # Per-species silhouettes and awake/sleeping/flying poses genuinely change pixels.
  page.evaluate("""()=>{const c=$('animal-picture').getContext('2d'),shapes=new Set();for(const d of NOCTURNAL_ANIMALS){const poses=[];for(const mode of ['wander','sleeping']){c.clearRect(0,0,400,230);drawAnimal(c,d.id,200,205,140,1,1,0,false,mode);poses.push($('animal-picture').toDataURL());}if(new Set(poses).size!==2)throw Error('缺少睡眠造型 '+d.id);shapes.add(poses[0]);if(habitat(d.id)==='air'){c.clearRect(0,0,400,230);drawAnimal(c,d.id,200,205,140,1,1,0,true);if($('animal-picture').toDataURL()===poses[0])throw Error('缺少飛行姿勢 '+d.id);}}if(shapes.size!==8)throw Error('造型重複');}""")
  # Night friends wake at dusk, sleep after dawn, retain individual times across reload.
  page.evaluate("worldTime=60;animals=NOCTURNAL_ANIMALS.map((d,i)=>makeAnimal(d.id,150+i*60,groundY(H*.7)));for(const a of animals){a.lifeLeft=120;a.nextEat=a.nextDrink=a.nextRest=a.nextSocial=999;}update(.02)")
  assert page.evaluate('animals.every(a=>a.mode==="sleeping")')
  assert page.evaluate("()=>{worldTime=200;update(.02);return animals.every(a=>a.mode!==\"sleeping\");}")
  assert page.evaluate("()=>{worldTime=30;update(.02);return animals.every(a=>a.mode===\"sleeping\");}")
  schedules=page.evaluate('animals.map(a=>({id:a.id,dawnSleep:a.dawnSleep,duskWake:a.duskWake}))');page.evaluate('save()');page.reload()
  assert page.evaluate('animals.map(a=>({id:a.id,dawnSleep:a.dawnSleep,duskWake:a.duskWake}))')==schedules
  assert page.evaluate('animals.length===8')
  # Owl/bat can chase in the air at night; feeding a porcupine and all 8 departures still work.
  assert page.evaluate("()=>{worldTime=200;animals=[makeAnimal('owl',200,groundY(H*.7)),makeAnimal('bat',330,groundY(H*.7))];const ok=startChase(...animals);for(let i=0;i<20;i++)update(.05);return ok&&animals.every(a=>isChasing(a)&&a.altitude>0);}")
  assert page.evaluate("()=>{worldTime=200;animals=[makeAnimal('porcupine',200,groundY(H*.7))];foods=[makeFood('broccoli',300,groundY(H*.7))];inviteToFood(foods[0]);for(let i=0;i<350;i++)update(.05);return foods.length===0;}")
  assert page.evaluate("()=>{worldTime=200;animals=NOCTURNAL_ANIMALS.map(d=>makeAnimal(d.id,200,groundY(H*.7)));for(const a of animals)a.lifeLeft=.1;for(let i=0;i<700;i++)update(.05);return animals.length===0;}")
  # Previously saved fennecs become foxes; removed difficult species no longer populate the scene.
  assert page.evaluate("""()=>{const old={version:3,worldTime:200,animals:['fennec','aardvark','serval','caracal','owl','lion'].map(id=>({id,x:.3,y:.5,lifeLeft:79})),foods:[],sky:[]};localStorage.setItem(STORE,JSON.stringify(old));animals=[];foods=[];skyItems=[];restore();save();return JSON.stringify(animals.map(a=>a.id))===JSON.stringify(['fox','owl','lion'])&&animals.every(a=>a.lifeLeft===79);}""")
  assert not errors,errors
  print(f'PASS {width}×{height} 八種問答發音放置／日夜題目與所有選項隔離／獨立洗牌無連續重複／八種姿勢像素／夜醒日睡與存檔／飛行追逐、餵食及離場')
  page.close()
 b.close()
