"""Verify generated audio samples and music controls; server must be running."""
import sys
import base64
from pathlib import Path
from playwright.sync_api import sync_playwright
base=(sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8004').rstrip('/')
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(base+'/games/math/3.MultiplicationCastle/')
    page.evaluate("async()=>{window.g=(await import('./js/game.mjs')).game}")
    assert page.evaluate('g.audio.context===null')
    page.locator('#select-all').click()
    page.wait_for_function('g.audio.musicPlaying && g.audio.voices.size>0')
    assert page.evaluate("g.audio.context.state==='running'")
    print('PASS first gesture starts live original background music')
    page.locator('#start').click();page.locator('#pause').click()
    assert page.evaluate('!g.audio.musicPlaying && g.audio.voices.size===0')
    page.get_by_role('button',name='繼續遊戲').click();page.wait_for_function('g.audio.musicPlaying')
    page.locator('.compact-sound').click();assert page.evaluate('!g.audio.musicPlaying && !g.audio.enabled')
    page.locator('.compact-sound').click();page.wait_for_function('g.audio.musicPlaying')
    page.wait_for_function("g.phase==='playing'")
    page.evaluate("()=>{g.question.wrong=new Set([0,1]);g.showHint()}")
    assert page.evaluate("g.phase==='hint'&&!g.audio.musicPlaying")
    page.get_by_role('button',name='我想再試試').click();page.wait_for_function('g.audio.musicPlaying')
    page.evaluate("()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'))}")
    assert page.evaluate("g.phase==='paused'&&!g.audio.musicPlaying")
    page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,value:false})")
    page.get_by_role('button',name='繼續遊戲').click();page.wait_for_function('g.audio.musicPlaying')
    page.evaluate("()=>{g.battle.waves=g.battle.config.waves;g.battle.enemies=[];g.advance(.04)}")
    assert page.evaluate("g.phase==='won'&&!g.audio.musicPlaying")
    page.get_by_role('button',name='下一關').click();page.wait_for_function('g.audio.musicPlaying')
    assert page.evaluate('g.audio.voices.size<18')
    print('PASS mute, resume, hint, visibility, win and next level with no duplicate music loops')
    result=page.evaluate("""async()=>{
      const {AudioPlayer,MUSIC}=await import('./js/audio.mjs');
      const seconds=MUSIC.melody.length*MUSIC.stepSeconds+2;
      const context=new OfflineAudioContext(1,Math.ceil(seconds*22050),22050);
      const player=new AudioPlayer(true);player.context=context;player.musicGain=context.createGain();player.musicGain.gain.value=.7;player.musicGain.connect(context.destination);
      for(let i=0;i<MUSIC.melody.length;i++)player.scheduleMusicStep(i,.05+i*MUSIC.stepSeconds);
      const buffer=await context.startRendering();const samples=buffer.getChannelData(0);
      let sum=0,peak=0;for(const n of samples){sum+=n*n;peak=Math.max(peak,Math.abs(n))}
      const raw=new ArrayBuffer(44+samples.length*2),v=new DataView(raw);
      const text=(at,t)=>{for(let i=0;i<t.length;i++)v.setUint8(at+i,t.charCodeAt(i))};
      text(0,'RIFF');v.setUint32(4,36+samples.length*2,true);text(8,'WAVE');text(12,'fmt ');v.setUint32(16,16,true);v.setUint16(20,1,true);v.setUint16(22,1,true);v.setUint32(24,22050,true);v.setUint32(28,44100,true);v.setUint16(32,2,true);v.setUint16(34,16,true);text(36,'data');v.setUint32(40,samples.length*2,true);
      for(let i=0;i<samples.length;i++)v.setInt16(44+i*2,Math.round(samples[i]*32767),true);
      const bytes=new Uint8Array(raw);let binary='';for(let i=0;i<bytes.length;i+=8192)binary+=String.fromCharCode(...bytes.subarray(i,i+8192));
      return {peak,rms:Math.sqrt(sum/samples.length),seconds,wav:btoa(binary)};
    }""")
    assert result['rms']>.001 and 0<result['peak']<.25,result
    Path('/tmp/乘法小兵守城-音樂試聽.wav').write_bytes(base64.b64decode(result.pop('wav')))
    print('PASS complete score produces real non-clipping audio:',result)
    assert not errors,errors
    browser.close()
