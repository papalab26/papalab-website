為 Papa-Lab 新增獨立、免費的 Blender 3D 資產製作流程，供未來塔防遊戲使用。所有檔案位於 `3d-assets`；現有首頁、遊戲及部署設定沒有修改，請勿自動合併或部署。

已製作低多邊形 Q 版步槍兵，包含頭盔、制服、背心、雙手持步槍與 17 根骨頭。GLB 約 316 KB、1,776 個三角面、一個 SkinnedMesh／材質，含 Idle、Walk、Aim、Shoot、Hit、Death 六種非空動畫；一併保存 .blend、建模腳本、初始化／重建腳本、MIT 授權、繁體中文 README 及獨立預覽。

驗證：Blender 4.3.2 headless 建模及 GLB 匯出重複執行成功；Khronos glTF Validator 零錯誤／零警告；Three.js 真實 WebGL 載入與六種動畫取樣播放、獨立骨架複製、100 名渲染（102 個繪圖呼叫）、手機尺寸及單檔 HTML 內容測試通過。報告與截圖位於模型資料夾。

限制：未測試實體手機效能、Babylon.js、全新雲端環境還原及官方 Blender 備援下載路徑。單檔內容已測試，雲端 Chromium 管理政策禁止 file:// URL，未宣稱本地 URL 開啟成功。本次沒有整合現有 2D 塔防遊戲；未安裝／驗證 Blender MCP，也未使用付費 AI 服務。
