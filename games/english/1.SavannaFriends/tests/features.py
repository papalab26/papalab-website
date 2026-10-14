import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for mobile in (False,True):
   context=await browser.new_context(viewport={'width':390 if mobile else 1280,'height':844 if mobile else 850},is_mobile=mobile,has_touch=mobile)
   await context.add_init_script("window.spoken=[];speechSynthesis.speak=u=>spoken.push(u.text);speechSynthesis.cancel=()=>{}")
   page=await context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   await page.route('**/*',lambda r:r.fulfill(body=(ROOT/'index.html').read_bytes(),content_type='text/html'))
   await page.goto('https://savanna.test/')
   await page.evaluate('skyQuestionAvailable=()=>false')
   assert await page.evaluate('ANIMALS.length')==24
   assert await page.evaluate('pond().rx')==320
   assert await page.locator('#species-total').inner_text()=='32'
   seen=[]
   # Every species goes through the real quiz, selection, pronunciation and placement flow.
   for i in range(24):
    await page.locator('#add').click();q=await page.evaluate('question.id');seen.append(q)
    opts=await page.locator('.option').evaluate_all('(els)=>els.map(e=>e.dataset.id)')
    assert len(set(opts))==4 and q in opts
    await page.locator(f'.option[data-id="{q}"]').click();assert await page.evaluate('spoken.at(-1)===question.word')
    await page.locator('#confirm').click()
    where=await page.evaluate("()=>{const p=pond(),h=habitat(pending.id);return h==='water'||h==='shore'?{x:p.x/W,y:p.y/H}:{x:.20,y:.66}}")
    r=await page.locator('#scene').bounding_box()
    if q=='fish':
     await page.locator('#scene').click(position={'x':r['width']*.2,'y':r['height']*.65})
     assert await page.evaluate('pending!==null && animals.length==='+str(i))
    pos={'x':where['x']*r['width'],'y':where['y']*r['height']}
    if mobile:await page.locator('#scene').tap(position=pos)
    else:await page.locator('#scene').click(position=pos)
    assert await page.evaluate('pending===null && animals.length==='+str(i+1))
   assert len(set(seen))==24
   await page.reload();assert await page.evaluate('animals.length')==24
   # Five minutes: fish stays inside pond, all species rest, sleep and wake.
   result=await page.evaluate("""()=>{
    const originalMake=makeAnimal;makeAnimal=(...args)=>({...originalMake(...args),lifeLeft:9999});animals=ANIMALS.map((d,i)=>{const p=pond(),water=habitat(d.id)==='water'||habitat(d.id)==='shore';return fitHabitat(makeAnimal(d.id,water?p.x:100+i*30,water?p.y:groundY(H*.66)))});
    const rests=new Set(),sleeps=new Set(),woke=new Set();worldTime=20;let fishOutside=0,birdFlew=false;
    for(let i=0;i<6500;i++){update(.05);for(const a of animals){if(a.mode==='resting')rests.add(a.id);if(a.mode==='sleeping')sleeps.add(a.id);if(sleeps.has(a.id)&&a.mode!=='sleeping')woke.add(a.id);if(a.id==='fish'&&!inPond(a.x,a.y))fishOutside++;if(habitat(a.id)==='air'&&a.altitude>10)birdFlew=true;}}
    return {rests:[...rests],sleeps:[...sleeps],woke:[...woke],fishOutside,birdFlew};
   }""")
   assert result['fishOutside']==0 and result['birdFlew'],result
   assert len(result['rests'])==24 and len(result['sleeps'])==24 and len(result['woke'])==24,result
   # Tap wakes a resting animal; label remains beside it and voice still plays.
   await page.evaluate("animals=[makeAnimal('elephant',230,groundY(H*.67))];animals[0].sleepAt=200;worldTime=230;update(.05);render()")
   assert await page.evaluate("animals[0].mode==='sleeping'")
   r=await page.locator('#scene').bounding_box()
   await page.locator('#scene').click(position={'x':r['width']*.23,'y':r['height']*.67-10})
   assert await page.evaluate("animals[0].action>0 && animals[0].mode==='wander' && spoken.at(-1)==='elephant'")
   assert await page.locator('#entity-word').inner_text()=='elephant'
   # Answer overlay freezes all clocks, including rest and sleeping logic.
   await page.locator('#add').click();before=await page.evaluate('JSON.stringify({animals,worldTime})');await page.evaluate('update(3)')
   assert before==await page.evaluate('JSON.stringify({animals,worldTime})')
   await page.locator('#close').click()
   # All poses are actually different pixels, without external art or WebGL.
   await page.evaluate("""()=>{
    const c=$('animal-picture').getContext('2d');for(const d of ANIMALS){const states=[];for(const mode of ['wander','resting','sleeping']){c.clearRect(0,0,400,230);drawAnimal(c,d.id,200,205,['giraffe','ostrich','flamingo'].includes(d.id)?110:140,1,0,0,false,mode);states.push($('animal-picture').toDataURL())}if(new Set(states).size<2)throw Error('缺少休息姿勢 '+d.id)}
   }""")
   # Prepare a readable screenshot with land friends, water friends and birds.
   await page.evaluate("""()=>{worldTime=60;animals=ANIMALS.map((d,i)=>{const p=pond(),h=habitat(d.id);const a=makeAnimal(d.id,h==='water'||h==='shore'?p.x-90+(i-6)*55:100+(i%6)*130,h==='water'||h==='shore'?p.y+(i%2?12:-12):groundY(H*.65));fitHabitat(a);a.wait=999;a.nextDrink=999;a.nextEat=999;a.nextRest=999;return a});animals[1].mode='resting';animals[1].activityLeft=999;foods=[makeFood('carrot',220,groundY(H*.84)),makeFood('corn',390,groundY(H*.84))];updateCounts();render()}""")
   await page.screenshot(path='/tmp/savanna-pond-mobile.png' if mobile else '/tmp/savanna-pond-desktop.png')
   await page.evaluate('animals[0].sleepAt=200;worldTime=230;update(.05);render()');await page.screenshot(path='/tmp/savanna-pond-night.png')
   await page.set_viewport_size({'width':844,'height':390});await page.wait_for_timeout(80)
   assert await page.evaluate("animals.filter(a=>a.id==='fish').every(a=>inPond(a.x,a.y))")
   assert not errors,errors
   print('PASS', '手機' if mobile else '桌面', '24 種問答／發音／放置、魚棲地限制與存檔、全部休息／深夜睡眠／醒來、鳥飛動、觸控喚醒、名稱位置、答題暫停、姿勢像素與橫向調整')
   await context.close()
  await browser.close()
asyncio.run(main())
