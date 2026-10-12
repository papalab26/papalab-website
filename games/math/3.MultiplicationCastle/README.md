# 乘法小兵守城

繁體中文靜態乘法遊戲，包含五關、範圍選擇、獨立士兵攔截、提示、音效與結算。無後端、無第三方素材與執行依賴。網站沿用既有 GitHub Pages 部署：更新合併或推送到 `main` 後，由 GitHub Pages 發布。

## 試玩

從儲存庫根目錄執行：

```sh
python3 -m http.server 8000
```

瀏覽器開啟 `/games/math/3.MultiplicationCastle/`。以本機 HTTP 服務提供模組；直接用檔案總管開啟這個模組版 `index.html` 可能受到瀏覽器限制。下載的單檔試玩版已內嵌 CSS 和 JavaScript，可離線直接開啟。

產生單檔試玩版：

```sh
python3 games/math/3.MultiplicationCastle/build_preview.py /tmp/multiplication-castle-preview.html
```

選擇乘法後按「開始遊戲」。按四個答案或鍵盤 1～4；答對幾就出幾名小兵。答錯兩次可看分組提示。Esc 可暫停或恢復。切換分頁自動暫停，回來後需要手動恢復。

## 檔案

- `index.html`：開始畫面、戰場、答題、提示與結算的結構。
- `style.css`：明亮卡通介面，含手機直向、橫向、平板與電腦版面。
- `js/rules.mjs`：五關設定、敵軍調整公式、城堡生命與移動參數。
- `js/questions.mjs`：完整題庫、低中高三組、抽題與錯誤選項生成。
- `js/battle.mjs`：實際時間模擬、獨立出兵、追蹤、空間碰撞與勝敗。
- `js/art.mjs`：原創 Canvas 背景、城堡、小兵走路動畫與特效。
- `js/audio.mjs`：原創 100 BPM 木琴感循環旋律、柔和和弦與音效；共用開關，暫停或提示時停止，首次操作後啟用。
- `js/game.mjs`：介面、輸入防重複、localStorage、音效與流程控制。
- `tests/rules.test.mjs`：Node 內建測試，沒有套件依賴。
- `tests/browser.py`：Playwright 瀏覽器流程測試。

## 調整難度

敵方使用獨立的乘法題庫，第一個因數來自本次已選範圍，第二個因數為 1～9；每次實際出兵數量為「乘法答案 × 關卡敵軍倍率」：第一關 1 倍、第二關 1.3 倍、第三關 1.6 倍、第四關 1.9 倍、第五關 2.2 倍；每關增加首關兵力的 30%，最後四捨五入。例如敵方答對 3 × 7 = 21，五關分別出 21、27、34、40、46 人。倍率只影響敵方，我方仍出恰好答案數量。敵方低、中、高答案輪流抽題，敵我題库與抽題進度互相獨立；碰巧抽到同一道題仍可能發生。

在 `js/rules.mjs` 的 `LEVELS` 調整 `interval`（基準解題秒數）、`waves`（本關答題／出兵次數）和 `enemyMultiplier`（敵軍答案倍率）。`RULES.enemyThinkMin`、`enemyThinkMax` 目前為 0.65、1.4，敵方每次思考時間會在基準時間的 65%～140% 間隨機變動。五關基準為 12、11、10、9、8 秒；第一批仍於第 5 秒出兵。`battle.mjs` 的 `createEnemyPlan()` 在每關開始時生成獨立題目與時間表，總敵兵數按該次實際抽題計算。暫停及提示使用同一模擬時鐘，不會在背景答題或補出兵。重試會重新抽題，範圍保持不變。

城堡生命與我方出兵數量規則不變；雙方移動速度及抵消動畫參數見下方說明。

## 驗證

```sh
node --test games/math/3.MultiplicationCastle/tests/rules.test.mjs
python3 games/math/3.MultiplicationCastle/tests/browser.py http://127.0.0.1:8000
```

音樂驗證與原創樂曲試聽檔輸出：

```sh
python3 games/math/3.MultiplicationCastle/tests/music.py http://127.0.0.1:8000
```

背景音樂在首次操作後啟動，共用的音樂／音效開關會記住設定。音樂只有既有遊戲畫格迴圈負責排程，暫停、提示、結算與切換分頁時會停止並清除已排程音符，沒有另外新增循環計時器。可在 `js/audio.mjs` 的 `MUSIC` 修改旋律、和弦與節奏；所有音樂均以 Web Audio 原創合成，不請求外部音樂資源。

第二個指令需先啟動上述伺服器，且需 Python Playwright 和 Chromium；本次雲端環境已有。腳本預設 Chromium 位於 `/usr/bin/chromium`。

15 組邏輯測試與 18 組瀏覽器驗證，包含 21／81 人出兵、一對一抵消、防線優先順序、敵方獨立乘法範圍、變動兵力與解題節奏、所有關卡批次與勝敗、儲存失敗復原、輸入防重複、暫停、提示、切換分頁、五關通關與 3,240 名小兵壓力測試。瀏覽器驗證使用真實點擊、觸控與鍵盤；漫長五關流程透過同一遊戲引擎加速模擬，分頁測試派送 visibilitychange 事件。這些不代表已在實體手機或所有瀏覽器完成測試。

目前雙方共用 `unitSpeed()`，均為每秒 11.44 邏輯像素；敵軍不受攔截約 50 秒抵達防線。我方會預判迎面敵人的相遇位置，避免同速時只追在敵方後面。小兵抵消仍即時生效，但會留下不參戰的角色殘影、煙霧與星星動畫；`RULES.cancelSeconds` 控制消失動畫長度，目前 1.2 秒。

敵我共用 `queueFormation()` 分組隊形：每組以三欄排列，組間分散，在 0.85 秒內陸續出場。敵方增加的兵力延伸為更多同樣大小的小隊，最後一隊可不足整組。尚未出場的敵兵也會阻止提前過關；暫停、換關或重試會正確凍結或清除出兵佇列。
