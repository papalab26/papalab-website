"""草地邊界放置、右下大池塘、答題音效與簡化提示的瀏覽器驗證。"""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for width,height in [(390,844),(844,390),(1280,850)]:
  page=browser.new_page(viewport={'width':width,'height':height},has_touch=True)
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content((ROOT/'index.html').read_text());page.wait_for_timeout(60)
  page.evaluate("""()=>{skyQuestionAvailable=()=>false;speechSynthesis.speak=()=>{};speechSynthesis.cancel=()=>{};
   window.notes=[];const original=AudioContext.prototype.createOscillator;
   AudioContext.prototype.createOscillator=function(){const osc=original.call(this),start=osc.start.bind(osc);osc.start=t=>{notes.push({frequency:osc.frequency.value,at:t});start(t)};return osc};}
  """)
  # Pixels just inside the drawn grass curve were previously rejected by a height box.
  for x in [100,500,850]:
   page.evaluate("bag=[animalDef('lion')]")
   page.locator('#add').click();assert page.locator('#quiz-title').inner_text()=="What's this?"
   wrong=page.locator('.option:not([data-id="lion"])').first
   if x==100:
    wrong.click();page.locator('#confirm').click();page.wait_for_timeout(80)
    assert page.locator('#feedback').inner_text()=='✗ 再試一次'
    assert page.evaluate('notes.length')==2
    assert page.evaluate('notes[0].frequency>notes[1].frequency && notes[1].at>notes[0].at')
    assert not page.locator('#quiz').is_hidden()
   page.locator('.option[data-id="lion"]').click();before=page.evaluate('notes.length')
   page.locator('#confirm').click();page.wait_for_timeout(80)
   assert page.evaluate('notes.length')==before+3
   assert page.evaluate('notes.at(-3).frequency<notes.at(-2).frequency && notes.at(-2).frequency<notes.at(-1).frequency')
   spot=page.evaluate(f'({{x:{x}/W,y:(grassTop({x})+12)/H}})')
   box=page.locator('#scene').bounding_box();page.locator('#scene').tap(position={'x':box['width']*spot['x'],'y':box['height']*spot['y']})
   assert page.evaluate('pending===null'),(width,x)
   assert page.evaluate(f'Math.abs(animals.at(-1).x-{x})<2 && Math.abs(animals.at(-1).y-(grassTop({x})+12))<2'),(width,x,page.evaluate('({a:animals.at(-1),edge:grassTop('+str(x)+')})'))
  # Sky and water still reject dry-land placements; correct audio can be muted.
  page.locator('#sound').click();page.evaluate("bag=[animalDef('lion')]");page.locator('#add').click()
  before=page.evaluate('notes.length');page.locator('.option:not([data-id="lion"])').first.click();page.locator('#confirm').click();page.wait_for_timeout(80)
  assert page.evaluate('notes.length')==before
  page.locator('.option[data-id="lion"]').click();page.locator('#confirm').click();page.wait_for_timeout(80)
  assert page.evaluate('notes.length')==before
  for pos in [{'x':.2,'y':.2},{'x':.9,'y':.96}]:
   page.locator('#scene').tap(position={'x':box['width']*pos['x'],'y':box['height']*pos['y']});assert page.evaluate('pending!==null')
  page.locator('#cancel').click();page.locator('#food').click();assert page.locator('#quiz-title').inner_text()=="What's this?";page.locator('#close').click()
  # Enlarged pool is clipped deliberately; fish stays visible while swimming.
  assert page.evaluate('pond().rx===320 && pond().x+pond().rx>W && pond().y+pond().ry>H')
  assert page.evaluate("""()=>{animals=[fitHabitat(makeAnimal('fish',pond().x,pond().y))];animals[0].lifeLeft=9999;worldTime=40;
   for(let i=0;i<6000;i++){update(.05);const a=animals[0];if(!inPond(a.x,a.y)||a.x<20||a.x>W-20||a.y>H-18)return false;}return true;}""")
  page.evaluate("worldTime=60;animals=[makeAnimal('lion',200,grassTop(200)+80),fitHabitat(makeAnimal('duck',760,H-60)),fitHabitat(makeAnimal('fish',850,H-45))];foods=[makeFood('carrot',400,H*.8)];render()")
  page.screenshot(path=f'/tmp/savanna-v4-{width}.png')
  assert not errors,errors
  print(f'PASS {width}×{height} 草地邊界放置／天空與水面拒絕／真實振盪器兩種提示及靜音／魚可見／簡化動物與食物題目')
  page.close()
 browser.close()
