"""實際點餐、用餐回應及排隊換客時的男女配音與裝置備援驗證。"""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':390,'height':844},has_touch=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.add_init_script('''window.spoken=[];window.testVoices=[
 {voiceURI:'male',name:'Microsoft Guy Online (Natural)',lang:'en-US'},
 {voiceURI:'female',name:'Microsoft Jenny Online (Natural)',lang:'en-US'},
 {voiceURI:'unknown1',name:'en-us-x-abc-local',lang:'en-US',localService:true},
 {voiceURI:'unknown2',name:'en-us-x-def-local',lang:'en-US',localService:true}
 ];window.SpeechSynthesisUtterance=function(text){this.text=text;};speechSynthesis.getVoices=()=>testVoices;speechSynthesis.speak=u=>spoken.push({text:u.text,voice:u.voice?.voiceURI,pitch:u.pitch,rate:u.rate});speechSynthesis.cancel=()=>{};''')
 page.route('https://chef-customer-voice.test/',lambda r:r.fulfill(body=(ROOT/'index.html').read_bytes(),content_type='text/html'));page.goto('https://chef-customer-voice.test/');page.locator('#start').click()
 assert page.evaluate("()=>{const people=Array.from({length:120},person);return people.some(p=>p.gender==='male')&&people.some(p=>p.gender==='female')&&people.every(p=>(p.gender==='male'?[1,3,4,5]:[0,2,6]).includes(p.style));}")
 page.evaluate("queue=[{...person(),gender:'male',style:4},{...person(),gender:'female',style:6},person(),person()]")
 page.locator('#order').click();assert page.evaluate("spoken.at(-1).voice==='male'&&spoken.at(-1).pitch===1")
 for item in page.evaluate('order'):page.locator(f'.food-card[data-id="{item}"]').click()
 page.locator('#serve').click();page.evaluate('clock=phaseStart+2.9');page.wait_for_function('reactionCue')
 assert page.evaluate("spoken.at(-1).text==='Yummy! Thank you!'&&spoken.at(-1).voice==='male'")
 page.evaluate('clock=phaseStart+reaction.duration+.02');page.wait_for_function("phase==='leaving'")
 page.evaluate('clock=phaseStart+1.1');page.wait_for_function("phase==='arriving'")
 page.evaluate('clock=phaseStart+.7');page.wait_for_function("phase==='serving'")
 assert page.evaluate("queue[0].gender==='female'&&spoken.at(-1).voice==='female'")
 page.locator('#levels').click();page.locator('#level-voice').click()
 assert page.locator('#voice-male option[value="female"]').count()==0
 assert page.locator('#voice-female option[value="male"]').count()==0
 assert page.locator('#voice-male option[value="unknown1"]').count()==1
 page.locator('#voice-male').select_option('unknown1');page.locator('#preview-male').click()
 assert page.evaluate("spoken.at(-1).voice==='unknown1'&&spoken.at(-1).pitch===1")
 page.locator('#voice-female').select_option('unknown2');page.locator('#preview-female').click()
 assert page.evaluate("spoken.at(-1).voice==='unknown2'")
 page.locator('#voice-done').click();page.locator('#close-levels').click();page.locator('#order').click()
 assert page.evaluate("spoken.at(-1).voice==='unknown2'")
 before=page.evaluate('spoken.length');page.locator('.food-card').first.click();assert page.evaluate('spoken.length')==before
 page.reload();assert page.evaluate("voiceChoices.male==='unknown1'&&voiceChoices.female==='unknown2'")
 # Names with unexposed gender remain unknown; never assume a locale-only voice is male/female.
 assert page.evaluate("voiceGender({name:'en-us-x-abc-local',lang:'en-US'})===null&&voiceGender({name:'English Female'})==='female'&&voiceGender({name:'English Male'})==='male'")
 page.evaluate("voiceChoices={male:'auto',female:'auto'};testVoices=[{voiceURI:'only',name:'Samantha',lang:'en-US',localService:true}];chooseVoice('male');renderVoiceChoices()")
 assert page.evaluate("voice.voiceURI==='only'") and '尚無可辨識的男聲' in page.locator('#voice-info').inner_text()
 page.evaluate("speak('Pizza.','male')");assert page.evaluate("spoken.at(-1).voice==='only'&&spoken.at(-1).pitch===1")
 page.evaluate("testVoices=[];speak('Pizza.','female')");assert page.evaluate("voice===null&&spoken.at(-1).voice===undefined&&spoken.at(-1).pitch===1")
 assert not errors,errors;print('PASS 角色外觀與性別設定／男客人點餐及用餐回應同男聲／排隊換女客人切女聲／分別指定試聽與儲存／未知語音不猜測／單一或缺少語音時備援且不變調／選項仍無聲（實機聲音未驗證）');b.close()
