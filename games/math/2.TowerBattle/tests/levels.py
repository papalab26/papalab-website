"""TowerBattle stage flow and real combat checks using the uploaded self-contained page."""
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1280,'height':800});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content((root/'index.html').read_text())
    assert '四關' in page.locator('.diff-sub').inner_text()
    page.locator('.dBtn-e').click()
    assert page.evaluate('currentLevel')==0
    assert page.evaluate('pHP===200&&cHP===60')
    names=['soldier','tank','airplane','robot']
    for level in range(4):
        page.evaluate('(level)=>startLevel(level)',level)
        page.evaluate('prepPhase=false;pPts=100;correctCount=1000;redraw()')
        unlocked=page.evaluate("['soldier','tank','airplane','robot'].filter(playerUnlocked)")
        assert unlocked==names[:level+1],(level,unlocked)
        for i,selector in enumerate(['#bS','#bT','#bA','#bR']):
            assert page.locator(selector).is_enabled()==(i<=level),(level,selector)
            assert page.locator(selector).is_visible()==(i<=level),(level,selector)
            before=page.evaluate('units.length');page.evaluate('(type)=>buy(type)',names[i])
            assert page.evaluate('units.length')==before+(i<=level)
        page.evaluate('units=[];gameFrames=5000;cpuSpawnCount=10;cPts=1000;for(let i=0;i<80;i++)cpuAI()')
        assert page.evaluate('units.every(u=>cpuUnlocked(u.type))')
        assert set(page.evaluate('units.map(u=>u.type)'))<=set(names[:level+1])
    print('PASS all four cumulative player/CPU unlocks; answering many questions cannot bypass stage locks')
    for level in range(4):
        page.evaluate('(level)=>{startLevel(level);gameOver(false)}',level)
        page.locator('#restBtn').click()
        assert page.evaluate('currentLevel')==level
        assert page.evaluate("pHP===levelCastleHP()&&cHP===levelCastleHP('cpu')&&units.length===0&&projs.length===0&&questionDelay===0")
        page.evaluate('gameOver(true)')
        page.locator('#restBtn').click()
        assert page.evaluate('currentLevel')==(level+1)%4
        assert page.evaluate('running&&units.length===0&&prepPhase')
    print('PASS defeat/retry, victory/next stage, final victory/replay, health and state reset')
    page.locator('#pauseBtn').click();page.locator('.pbtn-resume').click();assert not page.evaluate('paused')
    page.evaluate("questionDelay=400;endTimer=setTimeout(()=>gameOver(false),100);startVictoryFW();showDiff()")
    page.wait_for_timeout(200)
    assert page.evaluate('!running&&units.length===0&&endTimer===null&&questionDelay===0&&fwBurstTid===null')
    assert page.locator('#diffOv').is_visible() and not page.locator('#ov').is_visible()
    print('PASS pause/resume and menu clear old result/question/firework callbacks')
    page.locator('.dBtn-h').click()
    assert page.evaluate('curQ.ans>=2&&curQ.ans<=5&&currentLevel===0')
    for level in range(4):
        report=page.evaluate("""level=>{
          startLevel(level);let frames=0;
          for(;frames<30000&&running;frames++){
            if(!curQ.locked)choose(curQ.choices.indexOf(curQ.ans));
            if(!prepPhase){for(const type of ['robot','airplane','tank','soldier'])if(playerUnlocked(type)&&pPts>=UDEFS[type].cost){buy(type);break;}}
            stepFrame();
          }
          return {level:currentLevel,frames,playerHP:pHP,cpuHP:cHP,correct:correctCount,running};
        }""",level)
        assert report['cpuHP']==0 and report['playerHP']>0,report
        page.wait_for_timeout(850)
        assert page.locator('#ov').is_visible()
        assert '勝利' in page.locator('#ovtitle').inner_text() or '全部通過' in page.locator('#ovtitle').inner_text()
        print('PASS actual simulated combat win',report)
    page.locator('.result-menu').click();page.locator('.dBtn-e').click()
    for width,height in [(320,568),(390,844),(844,390),(1280,800)]:
        page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(100)
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,height)
        assert page.locator('#bS').bounding_box()['height']>=44 or width>980
    touch=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
    mobile=touch.new_page();mobile.set_content((root/'index.html').read_text());mobile.locator('.dBtn-e').tap()
    mobile.evaluate('prepPhase=false;pPts=3;redraw()');mobile.locator('#bS').tap()
    assert mobile.evaluate("units.some(u=>u.type==='soldier'&&u.side==='player')")
    mobile.locator('#pauseBtn').tap();mobile.locator('.pbtn-quit').tap();assert mobile.locator('#diffOv').is_visible()
    touch.close()
    assert not errors,errors
    print('PASS addition modes, phone/desktop layouts, touch purchase and no JavaScript errors')
    browser.close()
