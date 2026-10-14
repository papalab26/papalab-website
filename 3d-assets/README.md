# Papa-Lab 免費 3D 模型製作系統

本次成果集中在 `3d-assets`，使用 Blender 4.3.2 的 Python API 在 Codex Cloud 無介面模式自動建模。沒有付費 AI API、訂閱服務或外部模型生成服務。現有首頁、遊戲、CNAME、部署設定均未修改；不要直接合併或部署。

## 已執行成功的成果

- 自動建立低多邊形 Q 版步槍兵：頭盔、軍服、背心、背包、手腳、雙手持卡通步槍。
- Blender 來源 `models/rifleman/rifleman.blend`，完整建模程式 `scripts/build_rifleman.py`。
- GLB / glTF 2.0：`models/rifleman/rifleman.glb`，315,908 bytes；1,776 個三角面；17 根骨頭；一個 SkinnedMesh、一種頂點配色材質，沒有貼圖、Draco 壓縮、光源或遊戲地板。
- 模型腳底中心為原點，身高約 1.95 公尺；Blender +Z 向上、+Y 向前；匯出 GLB 為 +Y 向上、-Z 向前。
- 六種有實際關節變化的動畫，已透過 Three.js AnimationMixer 播放及取樣：

| 動畫名稱 | 長度 | 播放方式 | 動作 |
| --- | --- | --- | --- |
| Idle | 2 秒 | 循環 | 呼吸與頭部微動 |
| Walk | 1 秒 | 循環 | 原地步行、交替抬腿與身體微動 |
| Aim | 0.75 秒 | 單次、保留最後姿勢 | 舉槍瞄準 |
| Shoot | 0.5 秒 | 單次 | 槍身與上身後座力 |
| Hit | 約 0.583 秒 | 單次 | 後退及扭動反應 |
| Death | 1.5 秒 | 單次、保留最後姿勢 | 無血腥的卡通向後倒下 |

GLB 本身不指定循環次數；預覽與遊戲需按名稱設定 LoopRepeat／LoopOnce。Shoot 不包含子彈、傷害判定或音效。

## 查看模型，不需要安裝 Blender

最方便的是開啟 `preview/rifleman-standalone.html`：這是包含 Three.js 與 GLB 的單檔 HTML，可使用支援 WebGL 2 的 Chrome／Edge 查看；提供正面、斜俯視、六種動畫、暫停、重新播放、速度及 1／25／100 名士兵。

單檔內容已在 Chromium 執行與驗證。此雲端 Chromium 的管理政策阻擋 `file://` URL，因此測試透過直接載入 HTML 內容驗證；沒有把「在雲端直接開啟本地檔案 URL」列為成功。若你的瀏覽器也限制本地檔案，可使用下面的 HTTP 預覽。

在雲端 repository 中執行：

```sh
bash 3d-assets/scripts/serve.sh
```

服務連接埠為 8765，預覽路徑是 `/preview/`。若雲端介面有連接埠預覽功能，開啟該連接埠後前往此路徑；不要把 localhost 當作另一台裝置可直接存取的公開網址。也可設定 `PORT=8766`。預覽資源均保存在資料夾內，不需 CDN。

## 重複建立模型與環境

必要工具：Linux x64、Python 3、Node.js／npm。已有 Blender 4.3.x 時直接沿用；否則 `setup.sh` 下載免費官方 Blender 4.3.2 套件，核對官方 SHA256，解壓到忽略的 `.tools`，不修改系統 Blender。初始化需可連線至 `registry.npmjs.org`，官方備援下載需 `download.blender.org`。

```sh
bash 3d-assets/scripts/setup.sh
bash 3d-assets/scripts/build.sh
```

第一個命令實際建立測試立方體並匯出 GLB，使用鎖檔安裝免費的 Three.js、glTF Validator、esbuild，重新保存前端依賴及授權文件。第二個命令重新建模、製作動畫、匯出 GLB、標準驗證及更新單檔預覽。Blender 指令使用 `--python-exit-code 1`，Python 失敗會傳回非零狀態。

已安裝 Blender 的初始化路徑已執行成功；建模及匯出重複執行成功。**沒有測試刪除既有 Blender 後的官方下載分支，也尚未在全新 Codex 任務驗證環境還原。** 雲端安裝／啟動草稿已保存，但保存不是套用或發布；需在環境設定儲存與發布才會用於新環境。環境發布不會部署網站。

可在建模程式上方修改配色、部件、關節與動畫。每個部件先以單一骨頭權重綁定，再合併；目前是可重用的簡單卡通骨架，沒有 IK、手指或複雜布料模擬。輸出來源檔保留可修改骨架和六個 Action。部分 Blender 匯出記錄會提示未安裝選用 Draco，以及非 parent 的網格骨架；本模型未啟用 Draco，根節點網格則是刻意設計，GLB 標準與實際動畫播放驗證通過。

## 驗證證據

```sh
node 3d-assets/tests/validate_glb.mjs
# 先啟動 /preview/ 的 HTTP 服務
python3 3d-assets/tests/browser_test.py
# 不需要 HTTP，直接驗證嵌入模型的單檔內容
python3 3d-assets/tests/browser_test.py --standalone
```

瀏覽器測試需要 Python Playwright 與 `/usr/bin/chromium`，使用雲端軟體 WebGL 渲染；沒有關閉 TLS 驗證。測試檢查六種動畫名稱、每種動畫取樣後骨頭矩陣實際變化、腳底位置與身高、SkinnedMesh、獨立複製骨架、100 名渲染、手機尺寸控制與無 JavaScript 錯誤。截圖保存在模型資料夾。

- `build-report.json`：模型規格與動畫長度。
- `gltf-validation-report.json`：Khronos glTF Validator，零錯誤、零警告、零提示。
- `browser-test-report.json`：HTTP 版 Three.js 驗證。
- `standalone-test-report.json`：單檔內容驗證。
- 100 名士兵共 102 個繪圖呼叫（100 名 + 預覽地板 + 格線），每名只有一個。各名骨架及動畫時間獨立，幾何與材質共用。

尚未驗證：Babylon.js、實體手機 FPS、上百名在真實遊戲中的碰撞／尋路／渲染效能、重新建立的全新雲端環境。本次沒有改動塔防遊戲，不能把獨立預覽的成功當成已完成遊戲整合。

## Blender MCP 可行性

已閱讀開源第三方專案 [Blender MCP 說明](https://github.com/ahujasid/blender-mcp)。其一般流程是在 Blender 中安裝插件，配合長駐 socket 與 MCP server；官方文件有 Blender 介面與啟動插件操作。技術上可作為互動式工作流程的候選，但本次**沒有安裝，也沒有驗證 headless MCP**。

目前的直接 Blender Python API 已實現全部建模與動畫需求，不需要另設 MCP。該第三方專案也提供多種外部資產／AI 整合；本次完全未使用那些功能、API 或服務，避免另外付費及增加依賴。

## 未來整合現有塔防遊戲

現有遊戲使用 2D DOM／Canvas，不能直接用 `drawImage` 畫 GLB；需要另外加入 Three.js 或 Babylon.js 的 WebGL 渲染層，再把既有單位位置映射成 3D 地面座標。也可用 Blender 將六種動畫渲染成 2D sprite，保留既有 2D 渲染架構；本次沒有製作 sprite。

Three.js 已有成功的參考實作 `preview/preview.js`：

1. GLTFLoader 只載入一次，保存共用幾何、頂點色材質及 AnimationClip。
2. 使用 SkeletonUtils.clone 複製帶骨架的角色，不能只使用普通 scene.clone；每名有獨立 AnimationMixer。
3. Walk 是原地循環動畫；遊戲另外移動角色 root.position。面向平面目標向量 `(dx, dz)` 時，本模型 -Z 向前，可使用 `root.rotation.y = Math.atan2(-dx, -dz)`。
4. 待機／移動／瞄準／射擊／受擊狀態選相應動畫，透過短交叉淡化切換。射擊的傷害時點由遊戲邏輯控制；未使用動畫事件作實際傷害。
5. Death 以 LoopOnce 播放並停留；收到該動畫 finished 事件後從場景移除或回收單位，停止 Mixer。共用幾何／材質要等所有實例不再使用後才 dispose。
6. 手機先限制同時可見角色、避免陰影與獨立貼圖；更多單位需另外驗證 LOD、更新頻率、骨架動畫批次或實例化方案。一般 SkinnedMesh clone 不是 GPU InstancedMesh，本次沒有做 GPU 動畫實例化。
7. 未來制服／武器差異可改建模程式中的配色及部件再匯出；材質 multiply 可作整體色調，局部換色需修改頂點色或重新建模。武器目前綁在 Weapon 骨頭，便於替換。

## 授權與 Git 保存

Blender 是免費開源工具；建模不使用第三方人物素材。Papa-Lab 自製腳本、模型及動畫以 `LICENSE` 的 MIT 條款保存，便於遊戲重複使用。Three.js 授權保存在 `preview/vendor/LICENSE-three.txt`；驗證器和打包工具的來源／版本記錄在 package.json 與鎖檔，沒有把 node_modules 提交。

開發分支：`feat/3d-rifleman`。只提交 `3d-assets`，不包含既有英文遊戲的未提交檔案；不要自動合併。PR 描述保存在 `PR_DESCRIPTION.md`。如果 GitHub API 的環境存取尚未生效，推送分支仍可成功，但 PR 建立會被擋；請以實際 GitHub PR 編號確認是否已建立，不能把比較頁連結稱為已開 PR。
