// 將本地 Three.js 與 GLB 打包成不需要伺服器的單檔 HTML。
import { build } from 'esbuild';
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const result=await build({entryPoints:[resolve(root,'preview/preview.js')],bundle:true,minify:true,format:'iife',platform:'browser',write:false,legalComments:'eof'});
const model=readFileSync(resolve(root,'models/rifleman/rifleman.glb')).toString('base64');
let html=readFileSync(resolve(root,'preview/index.html'),'utf8');
html=html.replace(/<script type="importmap">[\s\S]*?<\/script>/,'');
const script=result.outputFiles[0].text.replace(/<\/script/gi,'<\\/script');
html=html.replace('<script type="module" src="./preview.js"></script>',()=>`<script>window.PAPALAB_MODEL_BASE64="${model}";</script><script>${script}</script>`);
writeFileSync(resolve(root,'preview/rifleman-standalone.html'),html);
console.log('已產生獨立 3D 預覽 HTML：',Buffer.byteLength(html),'bytes');
