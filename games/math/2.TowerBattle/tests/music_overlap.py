from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content((root/'index.html').read_text());page.locator('.dBtn-e').click()
    page.wait_for_function("bgRunning&&AC.state==='running'&&bgSources.size>0")
    page.evaluate("window.oldAnalyser=AC.createAnalyser();bgGain.connect(oldAnalyser)")
    page.wait_for_timeout(140)
    rms=page.evaluate("(()=>{const values=new Float32Array(oldAnalyser.fftSize);oldAnalyser.getFloatTimeDomainData(values);return Math.sqrt(values.reduce((s,v)=>s+v*v,0)/values.length)})()")
    assert rms>0.00001,rms
    print('PASS real background audio is playing, with only a short scheduling horizon')
    for stage in range(4):
        page.wait_for_function('bgSources.size>0')
        page.evaluate("""()=>{
          window.oldGain=bgGain;window.retired=[...bgSources];
          window.stopCount=0;for(const voice of retired){const original=voice.source.stop.bind(voice.source);voice.source.stop=when=>{stopCount++;return original(when)}};
          const gain=bgGain;const count=bgSources.size;for(let i=0;i<10;i++)startBgMusic();
          if(bgGain!==gain||bgSources.size!==count)throw new Error('Duplicate start created another music session');
          gameOver(true);
        }""")
        assert page.evaluate('!bgRunning&&bgGain===null&&bgSources.size===0&&oldGain.gain.value===0&&stopCount===retired.length')
        page.locator('#restBtn').click()
        page.wait_for_function('bgRunning&&bgGain!==oldGain&&bgSources.size>0')
        assert page.evaluate('bgGain!==oldGain&&oldGain.gain.value===0&&[...bgSources].every(v=>!retired.includes(v))')
        assert page.evaluate('currentLevel')==(stage+1)%4
    page.wait_for_timeout(250)
    assert page.evaluate("(()=>{const data=new Float32Array(oldAnalyser.fftSize);oldAnalyser.getFloatTimeDomainData(data);return data.every(v=>Math.abs(v)<.000001)})()")
    print('PASS four-stage transitions/replay cancel all old audio sources; the old output stays silent')
    page.locator('#pauseBtn').click();assert page.evaluate('!bgRunning&&bgSources.size===0&&bgGain===null')
    page.wait_for_timeout(300);assert page.evaluate('bgSources.size===0')
    page.locator('.pbtn-resume').click();page.wait_for_function('bgRunning&&bgSources.size>0')
    page.locator('#muteBtn').click();assert page.evaluate('muted&&!bgRunning&&bgSources.size===0')
    page.locator('#muteBtn').click();page.wait_for_function('!muted&&bgRunning&&bgSources.size>0')
    page.evaluate('bgIndex=BG_MELODY.length-1;bgNextAt=AC.currentTime+.01')
    page.wait_for_timeout(700)
    assert page.evaluate('bgIndex<5&&bgRunning&&bgSources.size<16')
    page.locator('#pauseBtn').click();page.locator('.pbtn-quit').click()
    assert page.evaluate('!running&&!bgRunning&&bgSources.size===0&&bgGain===null')
    assert not errors,errors
    print('PASS pause/resume, mute/unmute, score loop boundary and menu cleanup; no JavaScript errors')
    browser.close()
