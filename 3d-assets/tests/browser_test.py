"""透過真實 Three.js / WebGL 載入及取樣動畫；需要 Python Playwright。"""
import asyncio, json, sys
from pathlib import Path
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]
URL=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8765/preview/'
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--enable-unsafe-swiftshader','--use-gl=angle','--use-angle=swiftshader'])
  page=await browser.new_page(viewport={'width':1280,'height':900});errors=[];requests=[]
  page.on('request',lambda r:requests.append(r.url))
  page.on('pageerror',lambda e:errors.append(str(e)))
  if URL=='--standalone':
   await page.set_content((ROOT/'preview/rifleman-standalone.html').read_text())
  else: await page.goto(URL)
  await page.wait_for_function('window.riflemanPreview && riflemanPreview.units.length===1')
  await page.locator('#pause').click()
  result=await page.evaluate('''()=>{
   const p=riflemanPreview,T=p.THREE,u=p.units[0];const meshes=[];u.root.traverse(o=>{if(o.isSkinnedMesh)meshes.push(o)});
   const expected=['Idle','Walk','Aim','Shoot','Hit','Death'];if(p.clips.length!==6||!expected.every(n=>p.clips.some(c=>c.name===n)))throw Error('缺少動畫');
   if(meshes.length!==1)throw Error('預期只有一個 SkinnedMesh');const mesh=meshes[0];if(mesh.skeleton.bones.length!==17)throw Error('骨架不完整');
   const results={};function snapshot(){u.root.updateMatrixWorld(true);mesh.skeleton.update();return mesh.skeleton.bones.flatMap(b=>[...b.matrixWorld.elements])}
   for(const clip of p.clips){
    u.mixer.stopAllAction();const a=u.actions[clip.name];a.reset().setLoop(T.LoopOnce,1);a.clampWhenFinished=true;a.play();u.mixer.setTime(0);const first=snapshot();let delta=0;
    for(const t of [.13,.27,.51,.77,1]){u.mixer.setTime(clip.duration*t);const pose=snapshot();delta=Math.max(delta,...pose.map((v,i)=>Math.abs(v-first[i])))}
    if(delta<.001)throw Error('空白動畫 '+clip.name);results[clip.name]={seconds:clip.duration,tracks:clip.tracks.length,max_bone_matrix_change:delta};
   }
   u.mixer.stopAllAction();p.setAnimation('Idle',0);u.mixer.update(0);u.root.updateMatrixWorld(true);mesh.skeleton.update();mesh.computeBoundingBox();const bounds=mesh.boundingBox.clone();
   if(Math.abs(bounds.min.y)>.02||bounds.max.y<1.8||bounds.max.y>2.1)throw Error('比例／腳底原點不正確 '+bounds.min.y);
   // Verify two cloned skeletons do not share bones or animation time.
   p.populate(25);if(p.units[0].root===p.units[1].root)throw Error('複製失敗');let b0,b1;p.units[0].root.traverse(o=>{if(o.isSkinnedMesh)b0=o.skeleton.bones[0]});p.units[1].root.traverse(o=>{if(o.isSkinnedMesh)b1=o.skeleton.bones[0]});if(b0===b1)throw Error('骨架共用造成互相干擾');
   p.populate(100);for(const unit of p.units)unit.mixer.update(.2);p.renderer.render(p.scene,p.camera);const calls=p.renderer.info.render.calls;if(calls>103)throw Error('繪圖呼叫過多 '+calls);
   p.populate(1);const one=p.units[0];p.setAnimation('Walk',0);one.mixer.update(.17);p.setAnimation('Shoot',.18);one.mixer.update(.05);const mid=one.actions.Shoot.getEffectiveWeight();if(!(mid>0&&mid<1))throw Error('動畫沒有漸進混合');one.mixer.update(.2);if(one.actions.Shoot.getEffectiveWeight()<.99)throw Error('動畫切換未完成');p.setAnimation('Idle',0);return {animations:results,skinned_meshes:meshes.length,bones:mesh.skeleton.bones.length,foot_min_y:bounds.min.y,height:bounds.max.y,draw_calls_100:calls,webgl:p.renderer.capabilities.isWebGL2};
  }''')
  await page.locator('#front').click();await page.screenshot(path=str(ROOT/'models/rifleman/preview-front.png'))
  await page.locator('#top').click();await page.screenshot(path=str(ROOT/'models/rifleman/preview-top.png'))
  # Each animation can be selected from the interface and changes the rendered pose.
  images={}
  for name in ['Idle','Walk','Aim','Shoot','Hit','Death']:
   await page.locator('[data-clip="'+name+'"]').click()
   await page.evaluate('''name=>{const p=riflemanPreview,u=p.units[0],c=p.clips.find(c=>c.name===name);u.mixer.update(c.duration*(name==='Death'?1:.23));}''',name)
   await page.wait_for_timeout(80)
   images[name]=await page.locator('#stage canvas').screenshot()
   if name=='Death':await page.screenshot(path=str(ROOT/'models/rifleman/preview-death.png'))
  assert images['Idle']!=images['Walk'] and images['Idle']!=images['Shoot']
  await page.set_viewport_size({'width':390,'height':844});await page.locator('[data-clip="Idle"]').click();await page.wait_for_timeout(100)
  assert await page.locator('[data-clip="Walk"]').is_visible()
  await page.screenshot(path=str(ROOT/'models/rifleman/preview-mobile.png'))
  if URL=='--standalone':assert not requests,requests
  assert not errors,errors
  result['preview_mode']='standalone' if 'standalone' in URL else 'http'
  report_name='standalone-test-report.json' if result['preview_mode']=='standalone' else 'browser-test-report.json'
  (ROOT/'models/rifleman'/report_name).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
  print(json.dumps(result,ensure_ascii=False,indent=2));print('PASS：Three.js 讀取、六種非空動畫、獨立骨架、100 名繪圖、手機版面；無 JavaScript 錯誤。')
  await browser.close()
asyncio.run(main())
