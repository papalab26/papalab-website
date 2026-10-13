from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1280,'height':800});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content((root/'index.html').read_text());page.locator('.dBtn-e').click()
    assert page.evaluate('pPts===3&&pHP===200&&cHP===60')
    assert page.locator('#countHelp').count()==0
    for level,difficulty_name,low,high in [(0,'easy',2,5),(0,'hard',2,5),(1,'easy',2,10),(2,'hard',11,20)]:
        result=page.evaluate("""([level,diff])=>{
          difficulty=diff;startLevel(level);let previous=null,keys=new Set(),positions=new Set(),answers=[];
          for(let i=0;i<600;i++){newQ();if(curQ.key===previous)throw new Error('Repeated or reversed adjacent equation');previous=curQ.key;keys.add(curQ.key);positions.add(curQ.choices.indexOf(curQ.ans));answers.push(curQ.ans);if(new Set(curQ.choices).size!==4||curQ.choices.some(n=>n<1)||curQ.choices.filter(n=>n===curQ.ans).length!==1)throw new Error('Invalid options');}
          return {minimum:Math.min(...answers),maximum:Math.max(...answers),equations:keys.size,positions:positions.size};
        }""",[level,difficulty_name])
        assert result['minimum']==low and result['maximum']==high,result
        assert result['positions']==4,result
        assert result['equations']>=6,result
    print('PASS 2,400 questions: no adjacent/reversed repeats, complete number ranges and randomized valid choices')
    page.evaluate("difficulty='hard';startLevel(0)")
    original=page.locator('#qtext').inner_text()
    wrong=page.evaluate('curQ.choices.findIndex(n=>n!==curQ.ans)')
    page.locator('#c'+str(wrong)).click()
    assert page.locator('#qtext').inner_text()==original and page.locator('#c'+str(wrong)).is_disabled()
    page.wait_for_timeout(1100);assert page.locator('#qtext').inner_text()==original
    points=page.evaluate('pPts');correct=page.evaluate('curQ.choices.indexOf(curQ.ans)');page.locator('#c'+str(correct)).click()
    assert page.evaluate('pPts')==points+1
    assert page.locator('#cHpB').evaluate('(el)=>el.style.width')=='100%'
    print('PASS tutorial wrong-answer retry, uncluttered question panel, +1 point and full enemy health bar')
    report=page.evaluate("""()=>{
      startLevel(0);let frames=0;
      for(;frames<18000&&running;frames++){
        if(frames%300===0&&!curQ.locked)choose(curQ.choices.indexOf(curQ.ans));
        if(frames%300===150&&!prepPhase&&pPts>=1)buy('soldier');
        stepFrame();
      }
      return {seconds:frames/60,hp:pHP,enemyHP:cHP,answers:correctCount};
    }""")
    assert report['enemyHP']==0 and report['hp']>=160,report
    print('PASS slow novice simulation: one answer and one purchase per five seconds',report)
    for unit_type in ['tank','airplane','robot']:
        result=page.evaluate("""type=>{
          startLevel(3);paused=true;prepPhase=false;units=[];spawn(type,'player');units[0].x=430;units[0].artTick=0;render();const still=cv.toDataURL();units[0].artTick=12;render();const moved=cv.toDataURL();units[0].state='attack';units[0].fireAnim=12;render();const fired=cv.toDataURL();
          const tick=units[0].artTick;for(let i=0;i<10;i++)stepFrame();return {moves:still!==moved,fires:moved!==fired,pause:units[0].artTick===tick};
        }""",unit_type)
        assert all(result.values()),(unit_type,result)
    print('PASS tank/plane/robot animated pixels, attack feedback and pause freezing')
    page.evaluate("startLevel(3);prepPhase=false;paused=true;units=[];spawn('tank','player');spawn('airplane','player');spawn('robot','player');units[0].x=245;units[1].x=470;units[2].x=650;for(const u of units){u.artTick=12;u.fireAnim=8;}render()")
    page.mouse.move(0,0);page.screenshot(path='/tmp/tower-battle-animated-units.png')
    page.set_viewport_size({'width':390,'height':844});page.evaluate('startLevel(0);redraw()');page.wait_for_timeout(80)
    page.screenshot(path='/tmp/tower-battle-easy-first-level.png')
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert page.locator('#c3').bounding_box()['height']>=44
    assert not errors,errors
    print('PASS phone tutorial layout and no JavaScript errors')
    browser.close()
