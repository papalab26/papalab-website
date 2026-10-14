"""16 種蔬果的題庫、實際畫面、餵食與存檔驗證。"""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
EXPECTED=['carrot','corn','cabbage','broccoli','tomato','lettuce','apple','banana','orange','strawberry','watermelon','grapes','pineapple','pear','cucumber','pumpkin']
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for width,height in [(390,844),(844,390)]:
  page=b.new_page(viewport={'width':width,'height':height},has_touch=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.route('https://savanna-foods.test/',lambda r:r.fulfill(body=(ROOT/'index.html').read_bytes(),content_type='text/html'));page.goto('https://savanna-foods.test/')
  assert page.evaluate('VEGETABLES.map(f=>f.id)')==EXPECTED
  page.evaluate('window.spoken=[];speechSynthesis.speak=u=>spoken.push(u.text);speechSynthesis.cancel=()=>{}')
  seen=[]
  for _ in range(16):
   page.locator('#food').click();q=page.evaluate('question.id');seen.append(q)
   options=page.locator('.option').evaluate_all('(els)=>els.map(e=>e.dataset.id)')
   assert len(set(options))==4 and q in options and set(options)<=set(EXPECTED)
   page.locator(f'.option[data-id="{q}"]').click();assert page.evaluate('spoken.at(-1)===question.word')
   page.locator('#confirm').click();assert page.evaluate('pending.kind==="food"&&pending.id===question.id')
   area=page.locator('#scene').bounding_box();page.locator('#scene').tap(position={'x':area['width']*.20,'y':area['height']*.68})
   assert page.evaluate('foods.at(-1).id===question.id&&pending===null')
  assert set(seen)==set(EXPECTED),seen
  # Every new food gets eaten in five distinct steps; predatory animals remain uninterested.
  report=page.evaluate('''()=>{
   const results=[];for(const d of VEGETABLES.slice(6)){
    worldTime=60;animals=[makeAnimal('elephant',200,groundY(H*.7))];const a=animals[0];a.lifeLeft=120;a.nextDrink=a.nextRest=a.nextSocial=999;
    foods=[makeFood(d.id,260,a.y)];inviteToFood(foods[0]);let last=5,steps=[];
    for(let i=0;i<500&&foods.length;i++){update(.05);const n=foods.length?foods[0].bites:0;if(n!==last){steps.push(n);last=n;}}
    results.push({id:d.id,steps});
   }return results;
  }''')
  assert all(r['steps']==[4,3,2,1,0] for r in report),report
  assert page.evaluate("ALL_ANIMALS.filter(a=>['lion','cheetah','crocodile','owl'].includes(a.id)).every(a=>a.diet.length===0)")
  page.evaluate("foods=VEGETABLES.map(d=>makeFood(d.id,200,groundY(H*.7),3));animals=[];save()")
  page.reload();assert page.evaluate('foods.map(f=>f.id)')==EXPECTED
  assert page.evaluate('foods.every(f=>f.bites===3)')
  # Check distinct, non-empty silhouettes and actual geometric shrinking in rendered pixels.
  assert page.evaluate('''()=>{
   const canvas=document.createElement('canvas');canvas.width=240;canvas.height=220;const c=canvas.getContext('2d'),full=new Set();
   const count=()=>{const data=c.getImageData(0,0,240,220).data;let n=0;for(let i=3;i<data.length;i+=4)if(data[i]>100)n++;return n;};
   for(const d of VEGETABLES){c.clearRect(0,0,240,220);drawFood(c,d.id,120,190,145,5);const n=count();if(n<700)throw Error('食物缺少插畫 '+d.id);full.add(canvas.toDataURL());c.clearRect(0,0,240,220);drawFood(c,d.id,120,190,145,1);if(count()>=n*.5)throw Error('食物未縮小 '+d.id);}
   return full.size===16;
  }''')
  assert not errors,errors
  print(f'PASS {width}×{height} 16 種實際問答發音放置／四選項合法／新蔬果五口餵食／存檔還原／獨立造型與縮小')
  page.close()
 # Contact sheet renders the same Canvas illustrations used in the real quiz.
 page=b.new_page(viewport={'width':960,'height':880});page.set_content((ROOT/'index.html').read_text())
 page.evaluate('''()=>{const board=document.createElement('canvas');board.id='foods-art';board.width=960;board.height=880;board.style='position:fixed;inset:0;z-index:9999;background:white';document.body.append(board);const c=board.getContext('2d');c.fillStyle='#fffdf5';c.fillRect(0,0,960,880);for(let i=0;i<VEGETABLES.length;i++){const d=VEGETABLES[i],x=120+(i%4)*240,y=180+Math.floor(i/4)*220;drawFood(c,d.id,x,y,145,5);c.fillStyle='#365241';c.font='18px sans-serif';c.textAlign='center';c.fillText(d.word,x,y+26);}}''')
 page.locator('#foods-art').screenshot(path='/tmp/savanna-foods-art.png');b.close()
