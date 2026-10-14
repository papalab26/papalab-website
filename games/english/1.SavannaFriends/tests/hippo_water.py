"""河馬水中剪裁、水面接觸、尾流，以及題目插畫狀態隔離。"""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for width,height in [(390,844),(844,390)]:
  page=b.new_page(viewport={'width':width,'height':height},has_touch=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content((ROOT/'index.html').read_text())
  report=page.evaluate('''()=>{
   const cv=document.createElement('canvas');cv.width=400;cv.height=230;const c=cv.getContext('2d'),reports=[];
   const body=(x,y)=>{const p=c.getImageData(x,y,1,1).data;return p[3]>160&&p[2]>p[0]+3&&p[0]>p[1]+3;};
   for(const mode of ['wander','drinking','eating','resting','sleeping'])for(const dir of [-1,1]){
    c.clearRect(0,0,400,230);drawAnimal(c,'hippo',200,180,140,dir,.17,0,true,mode,true);let below=0,contact=0;
    for(let y=181;y<210;y++)for(let x=100;x<310;x++)if(body(x,y))below++;
    for(let x=150;x<250;x++)if(body(x,179))contact++;
    reports.push({mode,dir,below,contact});if(inPondDrawing!==false)throw Error('水中狀態洩漏');
   }
   c.clearRect(0,0,400,230);drawAnimal(c,'hippo',200,180,140,1,0,0,false,'wander',false);let landLegs=0;for(let y=170;y<179;y++)for(let x=150;x<250;x++)if(body(x,y))landLegs++;
   const snapshots=[];for(const phase of [0,.23]){c.clearRect(0,0,400,230);drawAnimal(c,'hippo',200,180,140,1,phase,0,true,'wander',true);snapshots.push(cv.toDataURL());}
   const actualEllipse=ellipse;let shadows=0;ellipse=(...args)=>{if(args[5]==='#3d5a3420')shadows++;return actualEllipse(...args);};c.clearRect(0,0,400,230);drawAnimal(c,'hippo',200,180,140,1,0,0,false,'wander',true);const waterShadows=shadows;drawAnimal(c,'hippo',200,180,140,1,0,0,false,'wander',false);ellipse=actualEllipse;
   return {reports,landLegs,animated:snapshots[0]!==snapshots[1],waterShadows,landShadows:shadows-waterShadows};
  }''')
  assert all(r['below']==0 and r['contact']>20 for r in report['reports']),report
  assert report['landLegs']>150 and report['animated'] and report['waterShadows']==0 and report['landShadows']==1,report
  # Exercise the actual scene renderer and then open an actual hippo question.
  page.evaluate("worldTime=60;speechSynthesis.speak=()=>{};speechSynthesis.cancel=()=>{};const q=pondPoint(.5);animals=[makeAnimal('hippo',q.x,q.y)];render();bag=[animalDef('hippo')];skyQuestionAvailable=()=>false")
  page.locator('#add').click();assert page.evaluate("question.id==='hippo'")
  assert page.evaluate('''()=>{const cv=document.createElement('canvas');cv.width=400;cv.height=230;drawAnimal(cv.getContext('2d'),'hippo',200,205,140,1,time,0,false);return cv.toDataURL()===$('animal-picture').toDataURL()&&inPondDrawing===false;}''')
  assert not errors,errors;print(f'PASS {width}×{height} 河馬水線接觸、下半身剪裁／水中無草地陰影／陸地腳恢復／尾流動畫／水中渲染後題目保持完整插畫');page.close()
 b.close()
