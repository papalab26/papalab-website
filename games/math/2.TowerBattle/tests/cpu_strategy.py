from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content((root/'index.html').read_text());page.locator('.dBtn-e').click()
    seconds=page.evaluate("""()=>{const random=Math.random;Math.random=()=>.5;try{return [cpuSolveSeconds({a:1,b:2,sum:3}),cpuSolveSeconds({a:5,b:4,sum:9}),cpuSolveSeconds({a:8,b:7,sum:15})]}finally{Math.random=random}}""")
    assert seconds==[3,4,5.5],seconds
    for mode in ['easy','hard']:
        for level in range(4):
            page.evaluate('([level,mode])=>{difficulty=mode;startLevel(level)}',[level,mode])
            result=page.evaluate("""()=>{let previous=null,seen=new Set();const original=JSON.stringify(curQ);for(let i=0;i<400;i++){nextCpuQuestion();if(cpuQuestion.key===previous)throw new Error('Repeating CPU question');previous=cpuQuestion.key;seen.add(cpuQuestion.key);const min=currentLevel===0?2:difficulty==='easy'?2:11,max=currentLevel===0?5:difficulty==='easy'?10:20;if(cpuQuestion.sum<min||cpuQuestion.sum>max||cpuQuestion.a+cpuQuestion.b!==cpuQuestion.sum)throw new Error('CPU range mismatch');}return {unchanged:original===JSON.stringify(curQ),diversity:seen.size}}""")
            assert result['unchanged'] and result['diversity']>=6,result
    print('PASS CPU independently draws selected-range questions; 1+2 averages 3s, 5+4 averages 4s')
    result=page.evaluate("""()=>{startLevel(1);const points=cPts;cpuQuestion={a:1,b:2,sum:3,key:'1+2',seconds:3};cpuSolveLeft=180;for(let i=0;i<179;i++)stepFrame();const before=cPts;stepFrame();return {points,before,after:cPts,answers:cpuAnswerCount}}""")
    assert result['before']==result['points'] and result['after']==result['points']+1 and result['answers']==1,result
    assert page.evaluate('prepPhase')
    page.locator('#pauseBtn').click();before=page.evaluate('cpuSolveLeft');page.wait_for_timeout(500);assert page.evaluate('cpuSolveLeft')==before
    page.locator('.pbtn-resume').click();page.evaluate('showDiff()');assert page.evaluate('cpuQuestion===null&&cpuSolveLeft===0&&cpuPlanQueue.length===0')
    print('PASS CPU earns exactly one point per completed answer, including prep; pause and menu cleanup')
    for level in range(1,4):
        history=page.evaluate("""level=>{startLevel(level);prepPhase=false;units=[];cPts=1000;for(let i=0;i<14;i++)cpuAI();return [...cpuPurchaseHistory]}""",level)
        expected=['soldier','tank','airplane','robot'][:level+1]
        assert set(history)==set(expected),(level,history)
        assert history[0]=='soldier' and history[1]==expected[-1],(level,history)
    result=page.evaluate("""()=>{startLevel(3);prepPhase=false;units=[];cpuSpawnCount=1;cpuPlanQueue=['robot','soldier'];cPts=3;cpuAI();const saved={points:cPts,count:units.length,plan:cpuPlanQueue[0]};cPts=10;cpuAI();return {saved,points:cPts,unit:units[0].type}}""")
    assert result=={'saved':{'points':3,'count':0,'plan':'robot'},'points':0,'unit':'robot'},result
    print('PASS varied unlocked troops, early aircraft/robot and saving rather than wasting points on soldiers')
    for level,newest in [(2,'airplane'),(3,'robot')]:
        report=page.evaluate("""level=>{startLevel(level);let elapsed=0;for(;elapsed<80*60;elapsed++){stepFrame();units=units.filter(u=>u.side==='cpu');}return {history:[...cpuPurchaseHistory],answers:cpuAnswerCount,points:cPts}}""",level)
        assert newest in report['history'],report
        print('PASS live scheduled CPU answers and purchases',level+1,report)
    result=page.evaluate("""()=>{startLevel(3);prepPhase=false;units=[];spawn('airplane','player');cpuSpawnCount=2;cpuPlanQueue=['tank','airplane','soldier'];cPts=5;cpuAI();return cpuPurchaseHistory.at(-1)}""")
    assert result=='airplane'
    assert not errors,errors
    print('PASS anti-air reaction and no JavaScript errors')
    browser.close()
