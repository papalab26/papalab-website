import { copyFileSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const files={'build/three.module.js':'three.module.js','build/three.core.js':'three.core.js','examples/jsm/loaders/GLTFLoader.js':'GLTFLoader.js','examples/jsm/controls/OrbitControls.js':'OrbitControls.js','examples/jsm/utils/BufferGeometryUtils.js':'BufferGeometryUtils.js','examples/jsm/utils/SkeletonUtils.js':'SkeletonUtils.js','LICENSE':'LICENSE-three.txt'};
mkdirSync(resolve(root,'preview/vendor'),{recursive:true});
for(const [src,dst] of Object.entries(files)){
 let content=readFileSync(resolve(root,'node_modules/three',src),'utf8');
 content=content.replaceAll('../utils/BufferGeometryUtils.js','./BufferGeometryUtils.js');
 writeFileSync(resolve(root,'preview/vendor',dst),content);
}
console.log('已保存 Three.js 0.180.0 與 MIT 授權；預覽不依賴 CDN。');
