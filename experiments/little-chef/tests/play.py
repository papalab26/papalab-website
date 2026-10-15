"""小小廚師：四關操作、收扣款時機、表情、語音呼叫、響應式及存檔測試。"""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'index.html').read_bytes()
def finish_reaction(page):
 page.evaluate('clock=phaseStart+reaction.duration+.02')
 page.wait_for_function("phase==='leaving'")
def next_customer(page):
 page.evaluate('clock=phaseStart+1.1')
 page.wait_for_function("phase==='arriving'||phase==='complete'")
 if page.evaluate("phase==='arriving'"):
  page.evaluate('clock=phaseStart+.7');page.wait_for_function("phase==='serving'")
def choose_order(page):
 for item in page.evaluate('order'):
  count=page.evaluate('spoken.length');page.locator(f'.food-card[data-id="{item}"]').click();assert page.evaluate('spoken.length')==count
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=b.new_page(viewport={'width':390,'height':844},has_touch=True);errors=[];requests=[]
 page.on('pageerror',lambda e:errors.append(str(e)));page.on('request',lambda r:requests.append(r.url))
 page.add_init_script("window.spoken=[];speechSynthesis.speak=u=>spoken.push(u.text);speechSynthesis.cancel=()=>{}")
 page.route('https://little-chef.test/',lambda r:r.fulfill(body=HTML,content_type='text/html'));page.goto('https://little-chef.test/')
 page.locator('#start').click();page.wait_for_function('[...foodImages.values()].every(i=>i.complete&&i.naturalWidth>0)')
 assert page.evaluate('money===30&&level===0&&queue.length===4')
 # Five real correct meals advance to the drink stage; only one credit per order.
 seen=[]
 for i in range(5):
  seen.append(page.evaluate('order[0]'));opts=page.locator('.food-card').evaluate_all('(els)=>els.map(e=>e.dataset.id)')
  assert len(set(opts))==3 and seen[-1] in opts
  before=page.evaluate('money');page.locator('#order').click();assert page.evaluate('spoken.at(-1)===def(order[0]).word')
  choose_order(page);assert page.locator('#serve').is_enabled();page.locator('#serve').click()
  assert page.evaluate('phase==="reacting"&&money==='+str(before))
  assert page.locator('#serve').is_disabled()
  finish_reaction(page);assert page.evaluate('money')==before+10
  page.evaluate('credit()');assert page.evaluate('money')==before+10
  next_customer(page)
 assert len(set(seen))==5 and page.locator('#win').is_visible() and page.evaluate('money===80&&progress[0]===5')
 page.locator('#next').click();assert page.evaluate('level===1&&DRINKS.some(d=>d.id===order[0])')
 # Wrong drink: no fee before the reaction finishes; queue advances once afterward.
 wrong=page.evaluate('options.find(d=>d.id!==order[0]).id');before=page.evaluate('money');seed=page.evaluate('queue[1].seed')
 page.locator(f'.food-card[data-id="{wrong}"]').click();page.locator('#serve').click()
 page.evaluate('clock=phaseStart+reaction.duration*.5');page.wait_for_timeout(80);assert page.evaluate('money')==before
 finish_reaction(page);assert page.evaluate('money')==before-10
 next_customer(page);assert page.evaluate('queue[0].seed')==seed
 # All requested dishes and drinks appear with real three-option selection and speech.
 for stage,pool in [(0,'FOODS'),(1,'DRINKS')]:
  for item in page.evaluate(pool+'.map(d=>d.id)'):
   page.evaluate('(n)=>startLevel(n)',stage)
   page.evaluate("id=>{deck=[def(id)];newOrder();}",item)
   assert page.evaluate('order[0]')==item
   assert page.locator('#order').inner_text()=='' and page.locator('#order svg').count()==1
   assert page.locator('#order').get_attribute('aria-label')=='播放客人訂單'
   page.locator('#order').click();assert page.evaluate('spoken.at(-1)')==page.evaluate('def(order[0]).word')
   count=page.evaluate('spoken.length');page.locator(f'.food-card[data-id="{item}"]').click();assert page.evaluate('spoken.length')==count
   page.locator('#serve').click();assert page.evaluate('reaction.good')
 # Real level chooser + base replacement + topping replacement + unordered matching.
 for stage in (2,3):
  page.evaluate('startLevel(0)');page.locator('#levels').click();page.locator(f'[data-level="{stage}"]').click()
  assert page.evaluate('level')==stage and page.locator('.food-card').count()==11
  assert page.locator('#order').inner_text()=='' and page.locator('#order').get_attribute('aria-label')=='播放客人訂單'
  page.locator('#order').click();assert page.evaluate('spoken.at(-1)===order.map(id=>def(id).word).join(", ")')
  assert page.locator('#serve').is_disabled()
  page.locator('.food-card[data-id="rice"]').click();page.locator('.food-card[data-id="bread"]').click()
  assert page.evaluate("selected.includes('bread')&&!selected.includes('rice')")
  page.evaluate('selected=[];updateUI()')
  # Choose in reverse order; ingredient order must not change correctness.
  for item in reversed(page.evaluate('order')):
   count=page.evaluate('spoken.length');page.locator(f'.food-card[data-id="{item}"]').click();assert page.evaluate('spoken.length')==count
  assert page.locator('#serve').is_enabled();page.locator('#serve').click();assert page.evaluate('reaction.good')
 # Exact symmetric money at zero; a wrong order may be a negative balance, no free failures.
 page.evaluate("startLevel(0);money=0;selected=[options.find(d=>d.id!==order[0]).id];updateUI()")
 page.locator('#serve').click();finish_reaction(page);assert page.evaluate('money===-10')
 # No binary 50/50 split: multiple random reactions, no consecutive identical pattern.
 report=page.evaluate("()=>{const ids=[];for(let i=0;i<80;i++)ids.push(chooseReaction().id);return {types:[...new Set(ids)],repeat:ids.some((x,i)=>i&&x===ids[i-1])};}")
 assert len(report['types'])==5 and not report['repeat'],report
 # Delayed discovery genuinely changes the customer face before money changes.
 report=page.evaluate('''()=>{
  startLevel(0);reaction={id:'gag',good:false,duration:4.9};phase='reacting';phaseStart=clock;const before=money,frames=[],greens=[];
  for(const t of [.4,1.6,2.5]){clock=phaseStart+t;draw();frames.push(canvas.toDataURL());const p=c.getImageData(Math.floor(canvas.width*.26),Math.floor(canvas.height*.38),Math.floor(canvas.width*.18),Math.floor(canvas.height*.21)).data;let green=0;for(let i=0;i<p.length;i+=4)if(p[i+1]>p[i]*1.025&&p[i]>100&&p[i+2]<170)green++;greens.push(green);}
  return {different:new Set(frames).size===3,greens,uncharged:money===before};
 }''')
 assert report['different'] and report['uncharged'] and report['greens'][1]>report['greens'][0]+200,report
 # Mute stops speech selection/replay and prevents a second music timer.
 page.evaluate('startLevel(0)');page.locator('#sound').click();assert page.evaluate('!sound&&musicTimer===null')
 spoken=page.evaluate('spoken.length');page.locator('#order').click();page.locator('.food-card').first.click();assert page.evaluate('spoken.length')==spoken
 page.locator('#sound').click();assert page.evaluate('sound&&musicTimer!==null')
 page.evaluate('money=60;progress=[2,3,0,0];save()');page.reload();assert page.evaluate('money===60&&progress[1]===3')
 assert not errors,errors
 assert not [url for url in requests if url.startswith('http') and not url.startswith('https://little-chef.test/')],requests
 print('PASS 四關實際點餐／八料理八飲料僅訂單發音／訂單只有圖示／選項靜音／配料替換與無序比對／正負10延後且單次結算／五單過關／排隊遞補／五種隨機反應與變臉像素／靜音與單音樂計時器／存檔／無外部資源與 JS 錯誤')
 page.close()
 for w,h in [(320,568),(390,844),(844,390),(1280,850)]:
  page=b.new_page(viewport={'width':w,'height':h},has_touch=True);page.on('pageerror',lambda e:errors.append(str(e)));page.set_content(HTML.decode())
  page.evaluate("window.spoken=[];speechSynthesis.speak=u=>spoken.push(u.text);speechSynthesis.cancel=()=>{}")
  page.locator('#start').click()
  for stage in range(4):
   page.locator('#levels').click();page.locator(f'[data-level="{stage}"]').click()
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(w,h,stage)
   for selector in ['#sound','#levels','#order','#serve']:
    rect=page.locator(selector).bounding_box();assert rect['width']>=44 and rect['height']>=44,(w,h,selector,rect)
   choose_order(page);page.locator('#serve').scroll_into_view_if_needed();page.locator('#serve').tap();assert page.evaluate('phase==="reacting"&&reaction.good')
   page.evaluate('clock=phaseStart+reaction.duration+.02');page.wait_for_function('phase==="leaving"');next_customer(page)
  if w==390:
   page.evaluate('startLevel(3)');page.screenshot(path='/tmp/little-chef-level4-mobile.png',full_page=True)
  assert not errors,errors;page.close();print(f'PASS {w}×{h} 四關觸控送餐／無橫向溢出／44px 主要操作區')
 b.close()
