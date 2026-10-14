"""池塘八種動物的浮水／涉水／水下畫面與題目隔離驗證。"""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
IDS=['duck','frog','turtle','fish','hippo','flamingo','crocodile','pelican']
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for width,height in [(390,844),(844,390)]:
  page=b.new_page(viewport={'width':width,'height':height},has_touch=True);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.set_content((ROOT/'index.html').read_text())
  report=page.evaluate('''ids=>{
   const cv=document.createElement('canvas');cv.width=400;cv.height=230;const c=cv.getContext('2d'),out=[];
   for(const id of ids)for(const mode of ['wander','resting','sleeping','drinking','eating'])for(const dir of [-1,1]){
    c.clearRect(0,0,400,230);drawAnimal(c,id,200,180,110,dir,.17,0,mode==='wander',mode,true);const p=c.getImageData(0,0,400,230).data;let below=0,contact=0,pixels=0,lowerPixels=0;
    for(let y=100;y<220;y++)for(let x=70;x<340;x++){const a=p[(y*400+x)*4+3];if(a>100){pixels++;if(y>180)lowerPixels++;}if(a>240&&y>180)below++;if(a>240&&y===179)contact++;}
    out.push({id,mode,dir,below,contact,pixels,lowerPixels});if(inPondDrawing!==false)throw Error('水中狀態洩漏 '+id);
   }
   const effects=[];for(const id of ids){const frames=[];for(const phase of [0,.23]){c.clearRect(0,0,400,230);drawAnimal(c,id,200,180,110,1,phase,0,true,'wander',true);frames.push(cv.toDataURL());}effects.push({id,animated:frames[0]!==frames[1]});}
   const real=ellipse;const shadows=[];for(const id of ids){let n=0;ellipse=(...args)=>{if(args[5]==='#3d5a3420')n++;return real(...args);};drawAnimal(c,id,200,180,110,1,0,0,false,'wander',true);const water=n;drawAnimal(c,id,200,180,110,1,0,0,false,'wander',false);shadows.push({id,water,land:n-water});}ellipse=real;
   return {out,effects,shadows};
  }''',IDS)
  assert all(r['pixels']>100 for r in report['out']),report
  assert all(r['below']==0 and r['contact']>=1 for r in report['out'] if r['id']!='fish'),report
  assert all(r['lowerPixels']>250 for r in report['out'] if r['id']=='fish'),[r for r in report['out'] if r['id']=='fish']
  assert all(r['animated'] for r in report['effects']),report
  assert all(r['water']==0 and r['land']==1 for r in report['shadows']),report
  # A real pond frame must not make subsequent quiz artwork lose legs or become translucent.
  for animal in IDS:
   assert page.evaluate('''id=>{worldTime=60;const q=pondPoint(.5);animals=[makeAnimal(id,q.x,q.y)];render();quizKind='animal';question=animalDef(id);bag=[question];skyQuestionAvailable=()=>false;nextQuestion();const cv=document.createElement('canvas');cv.width=400;cv.height=230;drawAnimal(cv.getContext('2d'),id,200,205,['giraffe','ostrich','flamingo','antelope'].includes(id)?110:140,1,time,0,false);return cv.toDataURL()===$('animal-picture').toDataURL()&&inPondDrawing===false;}''',animal)
  assert not errors,errors;print(f'PASS {width}×{height} 八種動物五種水中姿勢與方向／浮水或涉水接觸／魚完整水下透明度／水中無草地陰影／動態水紋氣泡／陸地與題目造型復原');page.close()
 b.close()
