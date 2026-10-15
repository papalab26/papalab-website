"""實際 Canvas 餐具／食物到嘴定位、咬下消失、飲料液面與吃後反應測試。"""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
CASES=[(0,['friedRice']),(0,['ramen']),(0,['pizza']),(0,['burger']),(0,['sushi']),(1,['orangeJuice']),(1,['coffee']),(2,['rice','egg']),(3,['bread','lettuce','cheese'])]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for width,height in [(390,844),(844,390),(1280,850)]:
  page=b.new_page(viewport={'width':width,'height':height});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content((ROOT/'index.html').read_text());page.evaluate('speechSynthesis.speak=()=>{};speechSynthesis.cancel=()=>{};startLevel(0)')
  page.wait_for_function('[...foodImages.values()].every(i=>i.complete&&i.naturalWidth>0)')
  for stage,items in CASES:
   report=page.evaluate('''([n,ids])=>{
    startLevel(n);order=[...ids];selected=[...ids];updateUI();submit();const balance=money,frames=[],imageFrames=[];
    const morsel=drawMorsel,drink=drawDrink;let actual=[];
    const record=(kind,consumed)=>{const m=c.getTransform();actual.push({kind,consumed,x:m.e,y:m.f,scale:Math.hypot(m.a,m.b)});};
    drawMorsel=(...args)=>{record('food',null);return morsel(...args);};drawDrink=(...args)=>{record('drink',args[2]);return drink(...args);};
    for(const t of [.35,.85,1.39,1.60,1.90,2.60]){clock=phaseStart+t;actual=[];draw();frames.push({t,actual:[...actual]});imageFrames.push(canvas.toDataURL());}
    drawMorsel=morsel;drawDrink=drink;const r=Math.min(150,H*.225),scale=canvas.width/W;
    return {frames,images:new Set(imageFrames).size,uncharged:money===balance,target:{x:W*.36*scale,y:(H*.48+r*.45)*scale},drink:n===1};
   }''',[stage,items])
   first=report['frames'][0]['actual'][0];middle=report['frames'][1]['actual'][0];mouth=report['frames'][2]['actual'][0];target=report['target']
   distance=lambda q:((q['x']-target['x'])**2+(q['y']-target['y'])**2)**.5
   assert distance(first)>distance(middle)>distance(mouth) and distance(mouth)<1,(width,height,items,report)
   assert report['images']==6 and report['uncharged'],report
   if report['drink']:
    sip=report['frames'][3]['actual'][0];returned=report['frames'][5]['actual'][0]
    assert sip['consumed']>mouth['consumed'] and returned['consumed']==1 and distance(returned)>20,report
   else:
    biting=report['frames'][3]['actual'][0]
    assert biting['scale']<mouth['scale']*.4 and not report['frames'][4]['actual'],report
  # A customer who rejects immediately must not take a bite.
  assert page.evaluate('''()=>{startLevel(0);selected=[options.find(d=>d.id!==order[0]).id];submit();reaction={id:'confused',duration:2.4,good:false};clock=phaseStart+1.39;return mealMotion(1.39)===null&&expression(1.39)==='confused';}''')
  # Delayed discovery: actual bite and chewing precede nausea/spitting, fee remains delayed.
  assert page.evaluate('''()=>{startLevel(0);selected=[options.find(d=>d.id!==order[0]).id];submit();reaction={id:'gag',duration:6.5,good:false};const before=money,poses=[];for(const t of [1.39,2.2,2.9,3.7]){clock=phaseStart+t;draw();poses.push(expression(t));}return JSON.stringify(poses)===JSON.stringify(['bite','chew','shockGreen','gag'])&&money===before;}''')
  page.evaluate('clock=phaseStart+reaction.duration+.02');page.wait_for_function("phase==='leaving'")
  assert page.evaluate('credited')
  assert not errors,errors;print(f'PASS {width}×{height} 九種料理飲料組合的實際食物／杯緣抵達嘴巴、食物咬下消失、杯中液面下降與放回／拒吃不進食／先咀嚼再變臉／金額延後結算');page.close()
 b.close()
