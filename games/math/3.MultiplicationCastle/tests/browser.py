"""Run against a local static server: python3 tests/browser.py http://127.0.0.1:8003"""
import sys
import time
from playwright.sync_api import sync_playwright
BASE = (sys.argv[1] if len(sys.argv) > 1 else 'http://127.0.0.1:8003').rstrip('/')
URL = BASE + '/games/math/3.MultiplicationCastle/'
passed = 0

def check(name, fn):
    global passed
    fn()
    passed += 1
    print(f'PASS {passed:02d} {name}', flush=True)

def snapshot(page, expression):
    return page.evaluate(expression)

def begin(page, tables=None):
    page.evaluate('(tables) => { if(tables) g.runTables=tables; g.totals=[];g.startLevel(0);g.advance(3);g.lastAttempt=-Infinity;g.inputReadyAt=0; }', tables)

def question(page, a=3, b=7):
    page.evaluate('([a,b])=>{g.deck={next:()=>({a,b,answer:a*b,key:`${a}x${b}`,options:[a*b,a*b+1,a*b+2,a*b+3]})};g.newQuestion();g.lastAttempt=-Infinity;g.inputReadyAt=0;}', [a,b])

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':1280,'height':850},locale='zh-TW')
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(URL, wait_until='networkidle')
    page.evaluate("async()=>{window.g=(await import('./js/game.mjs')).game}")
    def selection():
        assert page.locator('.table-button[aria-pressed=true]').count() == 4
        page.locator('#select-all').click()
        assert page.locator('.table-button[aria-pressed=true]').count() == 9
        for n in range(1,9): page.get_by_role('button',name=f'{n} 的乘法',exact=True).click()
        page.get_by_role('button',name='9 的乘法',exact=True).click()
        assert page.locator('.table-button[aria-pressed=true]').count() == 1
        assert page.locator('#selection-note').inner_text() == '至少選擇一種乘法喔！'
        page.reload();page.evaluate("async()=>{window.g=(await import('./js/game.mjs')).game}")
        assert page.locator('.table-button[aria-pressed=true]').count() == 1
        assert page.get_by_role('button',name='9 的乘法',exact=True).get_attribute('aria-pressed') == 'true'
    check('all select, final deselection guard, persisted range', selection)
    def storage():
        page.locator('.appbar .sound').click()
        assert page.locator('.appbar .sound').get_attribute('aria-pressed') == 'false'
        page.reload();page.evaluate("async()=>{window.g=(await import('./js/game.mjs')).game}")
        assert not snapshot(page,'g.soundOn')
        for value in [[],[0,9],['7'],None]:
            page.evaluate("(tables)=>localStorage.setItem('papalab-multiplication-castle-v1',JSON.stringify({tables}))",value)
            page.reload();page.evaluate("async()=>{window.g=(await import('./js/game.mjs')).game}")
            assert snapshot(page,'g.selected') == [2,3,4,5]
    check('sound persistence and invalid storage recovery',storage)
    def countdown():
        page.locator('#start').click()
        assert snapshot(page,'g.phase') == 'countdown'
        assert page.locator('.answer:disabled').count() == 4
        page.wait_for_function("g.phase==='playing'",timeout=4500)
        assert snapshot(page,'g.battle.time') < 1
    check('actual three-second countdown unlocks play', countdown)
    def correct():
        begin(page,[3]);question(page)
        page.locator('.answer').nth(0).click()
        assert snapshot(page,'g.round.summoned') == 21
        assert snapshot(page,'g.battle.allies.length+g.battle.pending.length') == 21
        assert page.locator('.answer:disabled').count() == 4
        assert '21 名小兵出發' in page.locator('#feedback').inner_text()
        page.wait_for_timeout(1000)
        assert snapshot(page,'g.battle.pending.length') == 0
        assert snapshot(page,'g.battle.allies.length') == 21
    check('mouse correct answer summons exactly 21 grouped soldiers',correct)
    def wrong_hint():
        begin(page,[3]);question(page)
        page.locator('.answer').nth(1).click()
        assert snapshot(page,'g.round.summoned') == 0 and snapshot(page,'g.battle.hp') == 10
        assert page.locator('.answer').nth(1).is_disabled()
        assert page.locator('#question').inner_text() == '3 × 7 = ?'
        page.wait_for_timeout(230);page.locator('.answer').nth(2).click()
        page.locator('#hint').click()
        assert snapshot(page,'g.phase') == 'hint'
        assert '7 + 7 + 7 = ?' in page.locator('.addition').inner_text()
        assert page.locator('.hint-group').count() == 3
        before = snapshot(page,'({time:g.battle.time,pending:g.battle.pending.length})')
        page.wait_for_timeout(700)
        assert before == snapshot(page,'({time:g.battle.time,pending:g.battle.pending.length})')
        page.get_by_role('button',name='我想再試試').click()
        assert page.locator('#question').inner_text() == '3 × 7 = ?'
        page.locator('.answer').nth(0).click()
        assert snapshot(page,'g.round.summoned') == 21
    check('wrong option disabled, two mistakes unlock paused grouping hint',wrong_hint)
    def keyboard():
        begin(page,[9]);question(page,9,9)
        page.keyboard.down('1')
        assert snapshot(page,'g.round.summoned') == 81
        page.wait_for_timeout(1200)
        page.keyboard.down('1')
        assert snapshot(page,'g.round.summoned') == 81
        page.keyboard.up('1');page.wait_for_timeout(220)
        page.keyboard.press('1')
        assert snapshot(page,'g.round.summoned') == 162
    check('81-unit keyboard summon; held key cannot answer next question',keyboard)
    def pointer_repeat():
        begin(page,[9]);question(page,9,9)
        page.locator('.answer').nth(0).click()
        for _ in range(4): page.locator('.answer').nth(0).dispatch_event('click',{'detail':1})
        assert snapshot(page,'g.round.summoned') == 81
        # A pointer held across a keyboard-confirmed question must not answer its successor.
        begin(page,[3]);question(page)
        box=page.locator('.answer').nth(0).bounding_box()
        page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2);page.mouse.down()
        page.keyboard.press('1');page.wait_for_timeout(1200);page.mouse.up()
        assert snapshot(page,'g.round.summoned') == 21
    check('repeated click and old pointer release cannot duplicate summons',pointer_repeat)
    def pause():
        begin(page,[9]);question(page,9,9);page.locator('.answer').nth(0).click()
        page.locator('#pause').click()
        before=snapshot(page,'({time:g.battle.time,pending:g.battle.pending.length,id:g.questionID,feedback:g.feedbackLeft})')
        page.wait_for_timeout(1100)
        assert before==snapshot(page,'({time:g.battle.time,pending:g.battle.pending.length,id:g.questionID,feedback:g.feedbackLeft})')
        page.get_by_role('button',name='繼續遊戲').click();page.wait_for_timeout(100)
        assert snapshot(page,'g.battle.time') < before['time']+.5
        assert snapshot(page,'g.battle.waves') == 0
    check('pause freezes units, spawning and question timer with no catch-up',pause)
    def visibility():
        begin(page,[3]);page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'))")
        assert snapshot(page,'g.phase')=='paused'
        before=snapshot(page,'g.battle.time');page.wait_for_timeout(350)
        assert snapshot(page,'g.battle.time')==before
        page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,value:false});document.dispatchEvent(new Event('visibilitychange'))")
        assert snapshot(page,'g.phase')=='paused'
        page.get_by_role('button',name='繼續遊戲').click()
    check('visibility loss automatically pauses and requires manual resume',visibility)
    def failure_retry():
        begin(page,[7])
        page.evaluate("g.battle.hp=1;g.battle.enemies=[g.battle.unit('enemy',350,600)];g.advance(.04)")
        assert snapshot(page,'g.phase')=='lost'
        assert page.locator('.answer:disabled').count()==4
        page.get_by_role('button',name='重新挑戰').click()
        assert snapshot(page,'({hp:g.battle.hp,time:g.battle.time,count:g.battle.allies.length,range:g.runTables})')=={'hp':10,'time':0,'count':0,'range':[7]}
        for level in range(1,5):
            page.evaluate('(level)=>{g.startLevel(level);g.advance(3);g.battle.hp=1;g.battle.enemies=[g.battle.unit("enemy",350,600)];g.advance(.04)}',level)
            assert snapshot(page,'g.phase')=='lost'
            page.get_by_role('button',name='重新挑戰').click()
            assert snapshot(page,'g.level')==level and snapshot(page,'g.battle.hp')==10
            assert snapshot(page,'g.battle.allies.length+g.battle.enemies.length+g.battle.pending.length')==0
        page.locator('#pause').click();page.get_by_role('button',name='回主選單').click()
        assert snapshot(page,'g.battle') is None and page.locator('#menu').is_visible()
    check('failure, retry and menu clear units and retain run selection',failure_retry)
    def five_levels():
        begin(page,[9])
        for level in range(5):
            page.evaluate("()=>{for(let i=0,n=Math.ceil(g.battle.config.total/81)+2;i<n;i++)g.battle.summon(9,9);g.advance(210)}")
            assert snapshot(page,'g.phase')=='won'
            assert snapshot(page,'g.battle.waves') == [6,7,8,9,10][level]
            assert snapshot(page,'g.battle.hp')>0
            if level<4:
                page.get_by_role('button',name='下一關',exact=True).click()
                assert snapshot(page,'g.level') == level+1
                assert snapshot(page,'g.battle.time') == 0
                assert snapshot(page,'g.battle.allies.length') == 0
                page.evaluate('g.advance(3)')
        assert '五關總統計' in page.locator('#dialog-content').inner_text()
        assert len(snapshot(page,'g.totals'))==5
        page.get_by_role('button',name='再玩一次',exact=True).click()
        assert snapshot(page,'g.level')==0 and snapshot(page,'g.totals.length')==0
    check('real simulation wins all five levels, final totals and replay',five_levels)
    def cpu_answers():
        begin(page,[1,2,3,4,5])
        plan=snapshot(page,'g.battle.enemyPlan')
        assert all(w['a'] in [1,2,3,4,5] and 1<=w['b']<=9 and w['count']==w['a']*w['b'] for w in plan)
        assert len(set(w['count'] for w in plan))>1
        snapshot(page,'g.advance(5)')
        wave=snapshot(page,'g.battle.lastEnemyAnswer')
        assert snapshot(page,'g.battle.enemies.length+g.battle.pending.filter(item=>item.unit.side==="enemy").length')==wave['count']
        snapshot(page,'g.updateHUD()')
        assert '上批 '+str(wave['count'])+' 人' in page.locator('#wave-info').inner_text()
        assert f"{wave['a']} × {wave['b']} = {wave['count']}" in page.locator('#battle-note').inner_text()
    check('CPU selected range, product armies and visible completed answer',cpu_answers)
    def large_army():
        begin(page,[9])
        result=page.evaluate("()=>{for(let i=0;i<40;i++)g.battle.summon(9,9);const start=performance.now();g.advance(1);g.renderer.draw(g.battle);return {count:g.battle.allies.length,ms:performance.now()-start}}")
        assert result['count']==3240
        assert result['ms']<3000,result
        print('  3,240 soldiers: one simulation second + render {:.1f} ms'.format(result['ms']),flush=True)
        assert not errors,errors
    check('3,240 independent soldiers simulate and render without errors',large_army)
    def desktop_layout():
        begin(page,[2,3,4,5])
        for width,height in [(1280,850),(1024,768),(768,1024),(390,844),(320,568),(844,390)]:
            page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(60)
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,height)
            for selector in ['#battle','#question','.answer:nth-child(4)','#pause']:
                box=page.locator(selector).bounding_box()
                assert box and box['y']>=0 and box['y']+box['height']<=height+1,(width,height,selector,box)
            canvas=page.locator('#battle').bounding_box(); wrap=page.locator('.canvas-wrap').bounding_box()
            assert canvas['height']<=wrap['height'] and canvas['y']+canvas['height']<=wrap['y']+wrap['height']+1,(width,height,canvas,wrap)
            for button in page.locator('.answer').all(): assert button.bounding_box()['height']>=44
    check('desktop, tablet, portrait and landscape fit with 44px+ answers',desktop_layout)
    def touch():
        touch_context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
        touch_page=touch_context.new_page();touch_page.goto(URL);touch_page.evaluate("async()=>{window.g=(await import('./js/game.mjs')).game}")
        begin(touch_page,[3]);question(touch_page)
        touch_page.locator('.answer').nth(0).tap()
        assert snapshot(touch_page,'g.round.summoned')==21
        touch_page.locator('#pause').tap();assert snapshot(touch_page,'g.phase')=='paused'
        touch_context.close()
    check('real touch taps answer and pause',touch)
    def denied_storage():
        denied=browser.new_context();denied.add_init_script("Object.defineProperty(window,'localStorage',{get(){throw new Error('blocked')}})")
        denied_page=denied.new_page();denied_page.goto(URL);denied_page.evaluate("async()=>{window.g=(await import('./js/game.mjs')).game}")
        assert snapshot(denied_page,'g.selected')==[2,3,4,5]
        denied_page.locator('#select-all').click();denied_page.locator('#start').click()
        denied_page.evaluate('g.advance(3)')
        assert snapshot(denied_page,'g.phase')=='playing'
        denied.close()
    check('blocked localStorage still supports selection and play',denied_storage)
    def focus():
        page.set_viewport_size({'width':1280,'height':850});begin(page)
        page.locator('#pause').click()
        assert page.locator('.app').evaluate('(el)=>el.inert')
        assert page.locator('#dialog-actions button').first.evaluate('(el)=>el===document.activeElement')
        page.keyboard.press('Shift+Tab')
        assert page.locator('#dialog-actions button').last.evaluate('(el)=>el===document.activeElement')
        page.keyboard.press('Escape')
        assert snapshot(page,'g.phase')=='playing'
    check('modal focus, background inertness and Escape resume',focus)
    check('no JavaScript errors during browser checks',lambda: (_ for _ in ()).throw(AssertionError(errors)) if errors else None)
    browser.close()
print(f'{passed} browser checks passed; no skipped checks.',flush=True)
