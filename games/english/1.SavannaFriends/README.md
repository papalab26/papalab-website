# 草原動物朋友 · Savanna Friends

Papa-Lab 基礎英文學習遊戲，正式遊戲目錄為 `games/english/1.SavannaFriends/`。以已確認的 v14 試玩版為基礎，後續精簡主畫面介面；獨立 Canvas 2D 單檔，無外部圖片、模型、字型或 CDN 程式庫。

## 遊玩

- 點動物圖示，看圖片選四個英文單字；點選可聽發音，確認答對後點場景放置。蔬果圖示開啟食物問答。
- 白天原本 24 種動物與飛機、直升機共 26 種等權洗牌，各平均約 3.85%。晚上只抽貓頭鷹、蝙蝠、狐狸、刺蝟、浣熊、老鼠、豪豬、Bushbaby，以及星星和流星；夜間天空題目機率約 25%。答案選項依時段篩選。
- 共 32 種動物，隨機慢走／加快、友善追逐、喝水、休息；夜行動物晚上活動、白天各自入睡。從放置起停留 60～120 秒後走／游／飛出畫面。食物依飲食偏好吸引朋友，五口逐次縮小後消失。
- 食物共 16 種：胡蘿蔔、玉米、高麗菜、綠花椰菜、番茄、萵苣，加上蘋果、香蕉、橘子、草莓、西瓜、葡萄、鳳梨、梨子、小黃瓜、南瓜。萵苣採狹長波浪葉與白色中肋，高麗菜採緊密圓球與包覆葉脈；蔬果保留自然輪廓與辨識特徵。新增食物沿用問答、發音、放置、五口縮小和存檔，並加入合適動物的食物偏好。
- 星星到天亮消失，流星短暫飛過；飛機／直升機往返 1 或 2 趟後飛走。
- 40 隻動物、20 份食物、12 個天空物件上限。答題及隱藏分頁時暫停活動倒數。動物名稱出現在身旁，主面板新增按鈕為圖示。
- 主畫面移除標題列，喇叭／靜音 SVG 按鈕位於草原右上角，只有圖示；保留無障礙標籤與 48px 觸控區域。
- 題目插畫等比例顯示，關閉按鈕在右上角；保留大觸控選項。

## 儲存與語音

使用裝置 `speechSynthesis` 英文語音與 Web Audio 答對／答錯音效。英文語音可用性由瀏覽器與系統語音決定，沒有付費語音 API。

`localStorage` key 為 `papalab-savanna-friends-pond-v3`，存動物、食物剩餘份量、日夜時鐘、天空飛行進度及停留時間。無此 key 時讀取舊 `papalab-savanna-friends-v1`。耳廓狐舊記錄轉成狐狸，已移除的土豚／藪貓／獰貓不再恢復。檔案試玩與正式網址的瀏覽器儲存彼此獨立；儲存不可用時仍可遊玩。

## 開發驗證

從專案根目錄執行下列腳本，需要 Python Playwright、Pillow 與 `/usr/bin/chromium`。不需要啟動外部服務；測試以本地 HTML 或 Playwright 路由執行。

```sh
python3 games/english/1.SavannaFriends/tests/features.py
python3 games/english/1.SavannaFriends/tests/art.py
python3 games/english/1.SavannaFriends/tests/regression.py
python3 games/english/1.SavannaFriends/tests/foods.py
python3 games/english/1.SavannaFriends/tests/placement_feedback.py
python3 games/english/1.SavannaFriends/tests/lifecycle.py
python3 games/english/1.SavannaFriends/tests/chasing.py
python3 games/english/1.SavannaFriends/tests/feeding_sky.py
python3 games/english/1.SavannaFriends/tests/nocturnal.py
```

包含桌面／手機直向與橫向的問答、發音呼叫、放置、存檔、日夜題庫隔離、姿勢像素、個別睡醒、變速與追逐、遠距離餵食、完整離場、天空生命週期及白天 260 次等權抽題。舊回歸測試在必要時延長測試動物停留時間或關閉額外抽題；自然生命週期與完整天空／夜晚題庫以獨立測試驗證。實體手機效能與語音聽感仍需實機確認。

主畫面精簡已以 320×568、390×844、844×390、1280×850 確認新增 50～60px 場景高度、圖示位置及切換、觸控尺寸、底部按鈕完整可見及放置過程不被聲音按鈕中斷；既有靜音音效／放置及餵食天空測試通過。

## 動物美術

32 種動物維持可愛 2D 自然插畫，加入柔和明暗、細輪廓與各物種特徵，並檢查走路、休息、睡覺與喝水等姿勢。完整檢視與逐項調整見 [動物畫風檢視](ART_REVIEW.md)。
