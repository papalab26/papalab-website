"""全動物六種姿勢、方向及繪圖狀態隔離的實際像素驗證。"""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1080});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content((ROOT/'index.html').read_text())
 result=page.evaluate('''()=>{
  const cv=document.createElement('canvas');cv.width=400;cv.height=230;const c=cv.getContext('2d');let frames=0;
  for(const d of ALL_ANIMALS)for(const mode of ['wander','resting','sleeping','drinking','eating','greeting'])for(const dir of [-1,1])for(const phase of [0,.17]){
   c.clearRect(0,0,400,230);const transform=c.getTransform().toString();drawAnimal(c,d.id,200,205,['giraffe','ostrich','flamingo','antelope'].includes(d.id)?110:140,dir,phase,mode==='greeting'?.8:0,mode==='wander',mode);
   if(c.__animalArt!==undefined||c.__sleepy!==undefined||c.getTransform().toString()!==transform)throw Error('繪圖狀態洩漏 '+d.id);
   const data=c.getImageData(0,0,400,230).data;let pixels=0;for(let i=3;i<data.length;i+=4)if(data[i]>150)pixels++;if(pixels<400)throw Error('空白造型 '+d.id+' '+mode);frames++;
  }
  // The new animal shading must not accidentally recolor food drawn afterward.
  const a=document.createElement('canvas'),b=document.createElement('canvas');a.width=b.width=400;a.height=b.height=230;const ac=a.getContext('2d'),bc=b.getContext('2d');drawAnimal(ac,'elephant',200,200,140,1,0,0,false);ac.clearRect(0,0,400,230);drawFood(ac,'lettuce',200,180,145,5);drawFood(bc,'lettuce',200,180,145,5);if(a.toDataURL()!==b.toDataURL())throw Error('動物材質影響食物');
  return frames;
 }''')
 print('PASS',result,'張：32 種動物×6 種姿勢×左右方向×2 個動畫階段；Canvas 狀態隔離與蔬果原色')
 assert not errors,errors;b.close()
