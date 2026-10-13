from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':390,'height':844});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content((root/'index.html').read_text());page.locator('.dBtn-e').click()
    ids=['bS','bT','bA','bR'];costs=[1,3,5,10]
    for level in range(4):
        page.evaluate('(level)=>{startLevel(level);prepPhase=false;redraw()}',level)
        assert page.evaluate('pPts')==[3,6,9,12][level]
        assert page.locator('.ub:visible').count()==level+1
        correct=page.evaluate('curQ.choices.indexOf(curQ.ans)');before=page.evaluate('pPts')
        page.locator('#c'+str(correct)).click();assert page.evaluate('pPts')==before+1
        for i in range(level+1):
            page.evaluate('(cost)=>{pPts=cost-1;redraw()}',costs[i])
            button=page.locator('#'+ids[i]);assert button.is_disabled()
            page.wait_for_function('(id)=>getComputedStyle(document.getElementById(id)).filter==="grayscale(1)"',arg=ids[i])
            assert button.evaluate("el=>el.classList.contains('ub-poor')&&getComputedStyle(el).filter==='grayscale(1)'")
            old=page.evaluate('units.length');page.evaluate('(type)=>buy(type)',['soldier','tank','airplane','robot'][i]);assert page.evaluate('units.length')==old
            page.evaluate('(cost)=>{pPts=cost;redraw()}',costs[i]);assert button.is_enabled()
            assert not button.evaluate("el=>el.classList.contains('ub-poor')")
            button.click();assert page.evaluate('pPts')==0 and page.evaluate('units.length')==old+1
            assert button.is_disabled()
        page.evaluate('gameOver(false)');page.locator('#restBtn').click();assert page.evaluate('pPts')==[3,6,9,12][level]
    print('PASS stage starting points, +1 rewards, retry reset, hidden units and exact affordability/gray restoration')
    for mode in ['easy','hard']:
        for level in range(4):
            result=page.evaluate("""([level,mode])=>{
              difficulty=mode;startLevel(level);const maximum=level===0?5:mode==='easy'?10:20,minimum=level===0||mode==='easy'?1:11;let high=0,low=100;
              for(let i=0;i<400;i++){newQ();const values=curQ.choices;if(values.some(v=>v<minimum||v>maximum)||new Set(values).size!==4||values.filter(v=>v===curQ.ans).length!==1)throw new Error('Options outside selected range');high=Math.max(high,...values);low=Math.min(low,...values);}
              return {high,low};
            }""",[level,mode])
            assert result['high']<=[5,10 if mode=='easy' else 20,10 if mode=='easy' else 20,10 if mode=='easy' else 20][level]
    print('PASS 3,200 questions: every choice within its practice range, four unique options and one correct answer')
    page.evaluate("difficulty='easy';startLevel(0);prepPhase=false;redraw()")
    page.screenshot(path='/tmp/tower-battle-hidden-units.png')
    page.evaluate("startLevel(3);prepPhase=false;pPts=3;redraw()")
    page.screenshot(path='/tmp/tower-battle-gray-units.png')
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert all(button.bounding_box()['height']>=44 for button in page.locator('.ub:visible').all())
    assert not errors,errors
    print('PASS phone control sizes and no JavaScript errors')
    browser.close()
