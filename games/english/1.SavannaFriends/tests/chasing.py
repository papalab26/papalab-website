"""變速、四種棲地的自動追逐，以及終止／暫停／存檔測試。"""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for width,height in [(390,844),(844,390),(1280,850)]:
  page=b.new_page(viewport={'width':width,'height':height},has_touch=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.route('https://savanna-chase.test/',lambda r:r.fulfill(body=(ROOT/'index.html').read_bytes(),content_type='text/html'));page.goto('https://savanna-chase.test/')
  page.evaluate("()=>{skyQuestionAvailable=()=>false;speechSynthesis.speak=()=>{};speechSynthesis.cancel=()=>{};let seed=81731;Math.random=()=>{seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;}}")
  result=page.evaluate("""()=>{
   worldTime=50;animals=[makeAnimal('elephant',100,groundY(H*.65))];const a=animals[0];a.lifeLeft=9999;a.nextSocial=a.nextRest=a.nextDrink=a.nextEat=9999;a.targetX=500;a.targetY=a.y;
   let speeds=[],smooth=true;for(let i=0;i<3000;i++){if(Math.abs(a.x-a.targetX)<10)a.targetX=a.targetX===500?100:500;
    const x=a.x,pace=a.pace;update(.02);if(Math.abs(a.x-x)>.005)speeds.push(Math.abs(a.x-x)/.02);if(Math.abs(a.pace-pace)>.07)smooth=false;}
   return {slow:Math.min(...speeds),fast:Math.max(...speeds),smooth};
  }""")
  assert result['slow']<12 and result['fast']>20 and result['smooth'],result
  # Actual social scheduler starts compatible pairs, including swimming and flying pairs.
  for h,ids in [('land',['lion','zebra']),('air',['bird','parrot']),('water',['fish','fish']),('shore',['duck','hippo'])]:
   result=page.evaluate("""([h,ids])=>{
    worldTime=60;const p=pond();animals=ids.map((id,i)=>fitHabitat(makeAnimal(id,h==='water'||h==='shore'?p.x-160+i*90:200+i*130,h==='water'||h==='shore'?p.y-15:groundY(H*.65))));
    for(const a of animals){a.lifeLeft=9999;a.nextRest=a.nextDrink=a.nextEat=9999;a.nextSocial=0;}
    const randomBefore=Math.random;Math.random=()=>.1;update(.02);Math.random=randomBefore;
    const started=animals[0].mode==='chaseLeader'&&animals[1].mode==='chaseFollower';const initial=animals.map(a=>({x:a.x,y:a.y}));let wrongHabitat=false,followed=false,distance=0;
    for(let i=0;i<700;i++){update(.02);const [a,b]=animals;if(h==='land'&&animals.some(a=>inPond(a.x,a.y)))wrongHabitat=true;if(h==='water'&&animals.some(a=>!inPond(a.x,a.y)))wrongHabitat=true;if(h==='shore'&&animals.some(a=>!nearPond(a.x,a.y)))wrongHabitat=true;
     if(b.mode==='chaseFollower'&&Math.hypot(b.targetX-a.x,b.targetY-a.y)<3)followed=true;
     distance=Math.max(distance,Math.hypot(a.x-b.x,a.y-b.y));if(animals.some(a=>a.x<0||a.x>W||a.y>H))wrongHabitat=true;}
    return {started,followed,wrongHabitat,moved:animals.every((a,i)=>Math.hypot(a.x-initial[i].x,a.y-initial[i].y)>5),ended:animals.every(a=>!isChasing(a)&&a.partner===null),distance};
   }""",[h,ids])
   assert result['started'] and result['followed'] and result['moved'] and result['ended'] and not result['wrongHabitat'],(h,result)
  # Keep a pair for interruption checks; pause the game during a real question overlay.
  page.evaluate("worldTime=60;animals=[makeAnimal('lion',200,groundY(H*.65)),makeAnimal('zebra',330,groundY(H*.65))];for(const a of animals){a.lifeLeft=9999;a.nextSocial=a.nextRest=a.nextEat=a.nextDrink=9999;}startChase(...animals)")
  page.locator('#add').click();snapshot=page.evaluate('JSON.stringify(animals.map(a=>({x:a.x,y:a.y,life:a.lifeLeft,mode:a.mode,pace:a.pace,activity:a.activityLeft})))')
  page.evaluate('update(5)');assert snapshot==page.evaluate('JSON.stringify(animals.map(a=>({x:a.x,y:a.y,life:a.lifeLeft,mode:a.mode,pace:a.pace,activity:a.activityLeft})))');page.locator('#close').click()
  assert page.evaluate("()=>{save();return JSON.parse(localStorage.getItem(STORE)).animals.length===2}")
  assert page.evaluate("()=>{worldTime=230;for(const a of animals)a.sleepAt=190;update(.05);return animals.every(a=>a.mode==='sleeping'&&a.partner===null)}")
  assert page.evaluate("()=>{worldTime=60;for(const a of animals){releaseAnimal(a);a.lifeLeft=999;}startChase(...animals);animals[0].lifeLeft=.01;update(.02);return animals[0].mode==='leaving'&&animals[1].mode==='wander'&&animals.every(a=>a.partner===null)}")
  page.evaluate("animals=[makeAnimal('lion',200,groundY(H*.65)),makeAnimal('zebra',330,groundY(H*.65))];startChase(...animals)")
  page.set_viewport_size({'width':height,'height':width});page.wait_for_timeout(80)
  assert page.evaluate('animals.every(a=>!isChasing(a)&&a.partner===null)')
  assert not errors,errors
  print(f'PASS {width}×{height} 隨機慢快速度／平滑加速／四棲地自動追逐與跟隨／結束清理／睡眠離場及旋轉中止／答題暫停及存檔')
  page.close()
 b.close()
