"""英文自然語音偏好、正常音高、試聽選擇、延後清單、持久化與選項無聲驗證。"""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844},has_touch=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_init_script('''window.spoken=[];window.testVoices=[];window.SpeechSynthesisUtterance=function(text){this.text=text;};speechSynthesis.getVoices=()=>testVoices;speechSynthesis.speak=u=>spoken.push({text:u.text,voice:u.voice?.voiceURI,lang:u.lang,rate:u.rate,pitch:u.pitch});speechSynthesis.cancel=()=>{};''')
 page.route('https://chef-voice.test/',lambda r:r.fulfill(body=(ROOT/'index.html').read_bytes(),content_type='text/html'));page.goto('https://chef-voice.test/')
 page.locator('#welcome-voice').click();assert page.locator('#voice-modal').is_visible()
 page.locator('#voice-preview').click();assert page.evaluate("spoken.at(-1).lang==='en-US'&&spoken.at(-1).pitch===1&&spoken.at(-1).rate===.95")
 # Voice lists commonly arrive after the first getVoices call.
 page.evaluate('''testVoices=[
 {voiceURI:'zh',name:'Chinese Natural',lang:'zh-TW',default:true,localService:true},
 {voiceURI:'old-us',name:'Microsoft David Desktop',lang:'en-US',localService:true},
 {voiceURI:'google-us',name:'Google US English',lang:'en-US'},
 {voiceURI:'uk',name:'Daniel',lang:'en-GB',localService:true},
 {voiceURI:'natural-us',name:'Microsoft Jenny Online (Natural)',lang:'en-US'}
 ];speechSynthesis.dispatchEvent(new Event('voiceschanged'));''')
 assert page.evaluate("voice.voiceURI==='natural-us'")
 assert page.locator('#voice-choice option').count()==5
 assert 'Chinese Natural' not in page.locator('#voice-choice').inner_text()
 page.locator('#voice-preview').click();assert page.evaluate("spoken.at(-1).voice==='natural-us'&&spoken.at(-1).pitch===1&&spoken.at(-1).rate===.95")
 page.locator('#voice-choice').select_option('uk');page.locator('#voice-preview').click()
 assert page.evaluate("spoken.at(-1).voice==='uk'&&spoken.at(-1).lang==='en-GB'")
 page.locator('#voice-done').click();assert page.locator('#welcome').is_visible()
 page.locator('#start').click();assert page.evaluate("spoken.at(-1).voice===(queue[0].gender==='female'?'natural-us':'uk')")
 count=page.evaluate('spoken.length');page.locator('.food-card').first.click();assert page.evaluate('spoken.length')==count
 page.locator('#levels').click();page.locator('#level-voice').click();assert page.locator('#voice-modal').is_visible()
 clock=page.evaluate('clock');page.wait_for_timeout(120);assert page.evaluate('clock')==clock
 page.keyboard.press('Escape');assert page.locator('#level-modal').is_visible() and page.locator('#voice-modal').is_hidden()
 page.keyboard.press('Escape');assert page.locator('#level-modal').is_hidden()
 page.reload();assert page.evaluate("voiceChoice==='uk'")
 page.evaluate("testVoices=[{voiceURI:'google-us',name:'Google US English',lang:'en-US'},{voiceURI:'uk',name:'Daniel',lang:'en-GB',localService:true}];speechSynthesis.dispatchEvent(new Event('voiceschanged'))")
 assert page.evaluate("voice.voiceURI==='uk'")
 page.locator('#welcome-voice').click();page.locator('#voice-choice').select_option('auto');assert page.evaluate("voice.voiceURI==='google-us'")
 # A higher quality GB voice can beat an old US desktop engine, and non-English is excluded.
 assert page.evaluate("()=>{testVoices=[{voiceURI:'old',name:'Microsoft David Desktop',lang:'en-US'},{voiceURI:'gb',name:'English UK Enhanced',lang:'en-GB'},{voiceURI:'zh',name:'Chinese Natural',lang:'zh-TW'}];chooseVoice();return voice.voiceURI==='gb';}")
 assert not errors,errors;print('PASS 自然英文優先／無中文混入／正常音高與 .95 語速／空清單備援及延後載入／試聽與手動切換／儲存與還原／關卡中設定暫停及焦點／選項仍不發音（未驗證實際聽感）');b.close()
