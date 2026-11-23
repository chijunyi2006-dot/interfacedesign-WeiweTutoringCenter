# 後端交接說明：行為紀錄（tracker）與意見回饋（Week10–11）

> 專題：雲林偉文補習班網站｜前端負責：蔡以琳｜對應課程：Week10 操作行為偵測、Week11 行為紀錄的雲端資料流程
> 這份交付 **不改你原本的 `school` App**，只「新增」一個叫 `tracking` 的 App，並「覆蓋」前端的 `templates/`、`static/`。
> 後端要做的事：複製、加兩行設定、`migrate`、部署，約 10 分鐘。

> **【2026-11-23 更新】`tracker_handoff` 現在已經是整合好的完整專案**：從原專案（`20261109`）複製了 `manage.py`、`myproject_core/`、`school/`、`requirements.txt`、`build.sh`、`.gitignore`，並已完成第 3 節步驟 2、3、5（加 `'tracking'`、`include('tracking.urls')`、CSRF／HTTPS 設定）。原專案資料夾沒有被修改。
> 另外 `settings.py` 的資料庫改成「有 `DATABASE_URL` 用它，沒有就用本機 SQLite」，連線字串（含密碼）不再寫在程式碼裡（第 8 節的資安建議）。**部署前請確認 Render 的環境變數已設定 `DATABASE_URL`（Neon 連線字串）**，否則線上會變成空的 SQLite。`requirements.txt` 由 UTF-16 轉成 UTF-8，內容不變。
> 也已把原專案 Week10 的兩個功能合併回前端：**榜單頁「各年度錄取人次」圖表**（Chart.js，跟著篩選更新，可切換長條／折線）與**課程頁「Email 驗證練習」表單**（只檢查格式，不送出、不儲存）。它們的操作紀錄改由新版 `tracker.js` 自動記錄，舊版加在每個連結上的 `onclick` 不再需要。改到的檔案：`base.html`（加 `{% block extra_head %}`）、`rankings.html`、`courses.html`、`course_detail.html`（搜尋框加 id）、`static/js/script.js`、`static/css/style.css`。

---

## 1. 一句話說明

使用者在網站上的操作（換頁、點按鈕、搜尋、篩選、停留時間）會由前端 `tracker.js` 記成一筆筆 JSON，**按下「開始測試」之後**，每一筆都會 POST 到後端 `/api/events/`，後端檢查後存進資料庫（Neon）。
另外，**首頁**頁尾多了「網站意見回饋」表單（有幫助／沒幫助＋意見，與簡報一致，只放首頁），會 POST 到 `/api/feedback/`，存進 `Feedback` 資料表。

```
使用者點擊 → tracker.js 記成 JSON → POST /api/events/ → Django 檢查 → 存進 Neon 的 tracking_uievent
使用者填意見 → feedback.js → POST /api/feedback/ → Django 檢查 → 存進 Neon 的 tracking_feedback
```

## 2. 壓縮檔內容（要複製到哪裡）

```
tracker交付_給後端/
├─ tracking/        ← 【新增】整個資料夾複製到 manage.py 旁邊（和 school/ 同一層）
│   ├─ models.py    UIEvent（操作紀錄）、Feedback（意見回饋）兩張表
│   ├─ views.py     receive_event、receive_feedback 兩個 API
│   ├─ urls.py      /api/events/、/api/feedback/
│   ├─ admin.py     後台可查看（唯讀）
│   ├─ migrations/0001_initial.py   已經產生好，不用 makemigrations
│   └─ tests.py     15 個自動測試
├─ templates/       ← 【覆蓋】整個資料夾覆蓋你的 templates/（新增 partials/tracker_bar.html、partials/feedback.html）
├─ static/          ← 【覆蓋】整個資料夾覆蓋你的 static/（新增 js/tracker.js、js/feedback.js；style.css 更新）
└─ 後端交接說明_Week11行為紀錄與意見回饋.md、tracker事件與欄位定義.md
```

**與你現有專案的差異（我已經比對過）**
- `templates/`：有改的是 `base.html`（多了 2 個 script、1 個 include 與 1 個 feedback 區塊）、`index.html`（只在最後多 1 行，引入意見回饋）、`partials/icons.html`（多了 2 個大拇指圖示），另新增 2 個 partial。其他頁面完全沒動。
- `static/js/script.js`：**完全沒改**，原功能不受影響。
- `static/css/style.css`：是前端最新版（導覽列區塊重新整理過，並加了測試面板與回饋區的樣式），直接覆蓋即可。

## 3. 整合步驟（照順序）

1. **複製檔案**：把 `tracking/` 放到專案根目錄；用壓縮檔裡的 `templates/`、`static/` 覆蓋原本的。
2. **`myproject_core/settings.py`**：`INSTALLED_APPS` 加一行：
   ```python
   'school',
   'tracking',   # Week11：操作紀錄與意見回饋
   ```
3. **`myproject_core/urls.py`**：加兩行
   ```python
   from django.urls import path, include   # 多 import include
   ...
   urlpatterns = [
       ...原本的路由...
       path('', include('tracking.urls')),   # /api/events/、/api/feedback/
   ]
   ```
4. **建表**（資料表的「施工圖」已經附好，不用 `makemigrations`）：
   ```bash
   python manage.py migrate
   ```
   這只會**新增** `tracking_uievent` 與 `tracking_feedback` 兩張表，不會動到 `school_*` 的任何資料。
   部署時 `build.sh` 已經會跑 `migrate`，推上 GitHub 後 Render 會自動對 Neon 建表。
5. **（建議）HTTPS 的 CSRF 設定**：目前 `settings.py` 沒有 `CSRF_TRUSTED_ORIGINS`／`SECURE_PROXY_SSL_HEADER`。
   Render 在前面處理 HTTPS，沒設的話，**所有 POST（登入、收藏、聯絡我們、這次的兩個 API）可能被擋成 403**。若線上 POST 出現 403，加上：
   ```python
   CSRF_TRUSTED_ORIGINS = ["https://*.onrender.com"]
   SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
   ```
6. **本機驗收**（見第 6 節），沒問題再 `git add . && git commit && git push`，等 Render 顯示 Live。
7. **Render 上線後再驗收一次**（本機的紀錄不會自動出現在雲端）。

> 靜態檔：你的設定用 WhiteNoise＋`collectstatic`，推上去後 Render 會自動重跑，不用手動處理。本機改完 JS 若沒更新，按 `Cmd＋Shift＋R` 強制重新整理。

## 4. API 規格

兩個 API 都：**只收 POST**、**要 CSRF token**（前端從 cookie `csrftoken` 取，放在 header `X-CSRFToken`）、Content-Type 為 `application/json`。
CSRF cookie 是靠 `base.html` 裡的 `{% csrf_token %}`（在 `partials/tracker_bar.html` 與 `partials/feedback.html`）讓 Django 在每一頁自動設定，**不需要**另外在 view 加 `@ensure_csrf_cookie`。

### 4-1 `POST /api/events/`（URL 名稱 `receive_event`）

請求（一筆事件）：
```json
{
  "event_id": "b3c1…",            // 必填，唯一，重送不會重複寫入
  "session_id": "7f2a…",          // 必填，同一次測試都一樣
  "seq": 2,                       // 必填，整數，這次測試的第幾筆
  "event_type": "filter_change",  // 必填
  "page_id": "courses",           // 必填
  "target_id": "filter_category", // 選填
  "occurred_at": "2026-11-16T05:20:31.000Z",  // 必填，含時區的 ISO 時間
  "ui_version": "v1",             // 選填
  "test_phase": "week11",         // 選填
  "data": {"result_count": 4}     // 選填，JSON 物件
}
```

| 結果 | HTTP | 回應 |
|---|---|---|
| 成功 | 200 | `{"success": true, "message": "事件已儲存", "id": 12}` |
| 同一個 `event_id` 重送 | 200 | `{"success": true, "message": "事件已存在", "id": 12}`（不重複寫入） |
| JSON 壞掉／不是物件／缺必填欄位／時間格式錯／`seq` 不是整數／`data` 不是物件 | 400 | `{"success": false, "message": "原因"}` |
| 請求超過 10,000 bytes | 413 | 同上 |

> 後端另外會：只保留 `data` 白名單欄位（與 tracker.js 相同，字串截到 60 字，其他欄位直接丟掉）；`seq` 必須是 0～2147483647 的整數（`true`、`2.7` 都會 400）；去掉文字裡的 NUL 字元（PostgreSQL 不接受）。
| 沒帶 CSRF token | 403 | Django 預設錯誤頁 |
| 用 GET 呼叫 | 405 | |

### 4-2 `POST /api/feedback/`（URL 名稱 `receive_feedback`）

請求：`{"page_id": "courses", "rating": "like", "comment": "找不到費用說明"}`

| 檢查 | 失敗回應（400） |
|---|---|
| `page_id` 必須在白名單：`home`、`courses`、`courses_detail`、`teachers`、`rankings`、`contact`、`member`、`login` | 頁面識別碼錯誤 |
| `rating` 必須是 `like` 或 `dislike` | 請選擇有幫助或沒幫助 |
| `comment` 不能空白 | 請填寫意見 |
| `comment` 不能超過 2000 字 | 意見不可超過 2000 字 |

成功：`{"success": true, "message": "感謝你的回饋，意見已儲存！", "id": 5}`。
目前只有首頁放表單；白名單在 `tracking/views.py` 的 `FEEDBACK_PAGES`，之後若其他頁面也要放意見回饋，把 `{% block feedback %}` 加到該頁模板（可參考 `index.html` 最後一行），並確認頁面代碼在白名單內。

## 5. 資料表

**`tracking_uievent`（操作紀錄，Model：`UIEvent`）**

| 欄位 | 型別 | 說明 |
|---|---|---|
| `id` | 自動 | 紀錄編號，API 回傳的 `id` 就是它 |
| `event_id` | 文字，唯一 | 單筆事件識別碼 |
| `session_id` | 文字 | 一次測試的識別碼 |
| `seq` | 整數 | 事件順序 |
| `event_type` | 文字 | 事件種類（見下表） |
| `page_id` | 文字 | 頁面代碼 |
| `target_id` | 文字，可空 | 元件代碼 |
| `occurred_at` | 日期時間 | 操作發生時間 |
| `ui_version` | 文字，可空 | 介面版本（目前 `v1`） |
| `test_phase` | 文字，可空 | 測試階段（目前 `week11`） |
| `data` | JSON | 補充資料 |
| `created_at` | 日期時間 | 資料庫寫入時間（自動） |

**`tracking_feedback`（意見回饋，Model：`Feedback`）**：`id`、`page_id`、`rating`（like／dislike）、`comment`、`created_at`。

**事件種類（`event_type`）**：`page_view`（進入頁面）、`page_duration`（頁面可見毫秒數）、`nav_click`（點連結換頁）、`button_click`（點按鈕）、`search`（搜尋，只記長度與筆數）、`filter_change`（換篩選）、`form_invalid`／`form_validated`（表單檢查）、`feedback_submit`（意見送出成功）。
每個欄位與事件的完整定義見 `tracker事件與欄位定義.md`。

**隱私**：不存搜尋文字、姓名、電話、Email、密碼。意見回饋的文字是使用者主動填寫，存在 `Feedback`，不會進操作紀錄。

## 6. 驗收步驟（本機與 Render 各做一次）

1. 開首頁，左下角點「操作紀錄」展開，按 **開始測試**。面板會顯示「本頁上傳：成功 N／失敗 0」。
2. 隨便操作：點導覽列、換篩選、開 LINE 對話框，再換頁。
3. 回到**首頁**，到頁尾送一則意見：選「有幫助／沒幫助」、輸入意見、按「送出回饋」。成功會顯示「回饋編號：N」。
4. 測失敗情況：不選評價、或意見留空，應顯示提示，資料庫筆數**不增加**。
5. 到資料庫核對（三選一）：
   - **Django 後台** `/admin/`：「操作紀錄」「意見回饋」兩個項目，可依事件種類、頁面篩選。
   - **Neon SQL Editor**：
     ```sql
     SELECT id, session_id, seq, event_type, page_id, target_id, data, occurred_at
     FROM tracking_uievent ORDER BY id DESC LIMIT 20;

     SELECT id, page_id, rating, comment, created_at
     FROM tracking_feedback ORDER BY id DESC LIMIT 10;

     -- 各種事件各幾筆
     SELECT event_type, COUNT(*) FROM tracking_uievent GROUP BY event_type ORDER BY 2 DESC;
     ```
   - **Django Shell**：`python manage.py shell` 後輸入 `from tracking.models import UIEvent; UIEvent.objects.order_by('-id')[:5]`
6. 瀏覽器開發者工具 → Network，找到 `events/` 請求：POST、狀態 200、Response 有 `success` 與 `id`；用這個 `id` 在資料庫找同一筆（Week11 簡報的驗收方式）。

**自動測試**：`python manage.py test tracking`，應顯示 `Ran 15 tests ... OK`（涵蓋儲存、重複、缺欄位、壞 JSON、錯誤時間、CSRF 403、意見驗證，以及 data 白名單、seq 範圍、NUL 字元、資料過大 413）。

## 7. 前端已測試／尚未測試

已測（前端預覽站，SQLite）：
- [x] 開始後每筆操作都上傳成功，資料庫欄位值與畫面一致（含 `page_view`、`filter_change`、`button_click`、`page_duration`、`feedback_submit`）
- [x] 意見回饋：未選評價、意見留空都不會存檔；成功後表單清空並顯示回饋編號
- [x] 後端 API 自動測試全部通過（原 10 個＋後端補強 5 個，共 15 個）
- [x] 手機寬度（375px）沒有橫向捲動
- [x] **在你現有專案的複本上整合測試**（加 `'tracking'`、`include`、`migrate`、`collectstatic`，用本機 SQLite，**沒有連到 Neon**）：6 個頁面都 200 且帶測試面板（回饋區只在首頁）；啟用 CSRF 檢查時，帶 cookie token 的兩個 API 都回 200；`manage.py check` 與 10 個測試通過

**尚未測：**
- [ ] 在 Neon PostgreSQL 與 Render 上的實際運作（需後端部署後一起測）
- [ ] 登入後的畫面與聯絡表單的 `form_invalid`／`form_validated` 紀錄
- [ ] 榜單網址：後端用 `/ranking/`，前端文件寫 `/rankings/`；tracker 與 feedback 已把兩者都統一記成 `rankings`，功能不受影響

## 8. 注意事項

- **資安提醒（請優先處理）**：`myproject_core/settings.py` 的 `DATABASES` 把 **Neon 連線字串（含密碼）直接寫成 `default=`**，而且程式碼已在 GitHub。
  這代表任何看得到 repo 的人都能連到你們的正式資料庫；另外，本機只要沒設 `DATABASE_URL`，`runserver`／`migrate` 就會**直接動到 Neon 的正式資料**。
  建議：(1) 到 Neon 重設資料庫密碼；(2) `default=` 改成 `sqlite:///db.sqlite3`，連線字串只放 Render 的環境變數 `DATABASE_URL`（教學文件步驟 10 的做法）；(3) 若 repo 是公開的，要改成私人或視為已外洩。這次整合測試我是用 `DATABASE_URL` 指到本機 SQLite 做的。

- **測試面板**（左下角「操作紀錄」）是給「做行為測試」用的。測試期間所有人都看得到；要正式上線隱藏時，把 `templates/base.html` 的 `{% include "partials/tracker_bar.html" %}` 那行註解掉即可，但 **CSRF 的 `{% csrf_token %}` 在 `feedback.html` 也有**，意見回饋仍能用。（隱藏面板後使用者就不能開始記錄，若要讓測試者自動記錄需另外討論。）
- **不要對正式資料庫執行 `loaddata demo_data`**（會覆蓋正式資料，教學文件已警告過）。這次交付不需要任何 fixture。
- 改介面版本時（例如 v2），改 `static/js/tracker.js` 最上方的 `UI_VERSION`；改測試階段改 `TEST_PHASE`。這兩個值會存進資料庫，才能比較改版前後。
- 後台的「操作紀錄」「意見回饋」為**唯讀**，避免誤改資料。
- `page_duration` 是「頁面可見的毫秒數」，不等於閱讀時間；停留久也可能是找不到資訊，解讀請保守（Week11 簡報第 38、62 頁）。

## 9. 常見錯誤對照

| 現象 | 原因 | 處理 |
|---|---|---|
| 面板顯示「失敗」，Console 出現 403 | CSRF 設定（Render 的 HTTPS） | 加第 3 節步驟 5 的兩行設定 |
| Console：`找不到 CSRF Token` | 頁面沒有輸出 `{% csrf_token %}`（沒覆蓋 templates） | 確認 `partials/tracker_bar.html` 有複製並被 `base.html` include |
| 404 `/api/events/` | 忘了在 `urls.py` 加 `include('tracking.urls')` | 補第 3 節步驟 3 |
| `no such table: tracking_uievent`／`relation ... does not exist` | 沒跑 `migrate` | `python manage.py migrate` |
| `NoReverseMatch: receive_feedback` | `INSTALLED_APPS` 或 `urls.py` 沒加好 | 回頭檢查步驟 2、3 |
| 首頁沒有樣式或沒有回饋區 | 沒覆蓋 `static/`、`templates/`，或 Render 還沒部署完 | 重新覆蓋後 push；本機按 `Cmd＋Shift＋R` |
| 回饋顯示「頁面識別碼錯誤」 | 新頁面沒加進 `FEEDBACK_PAGES` | 在 `tracking/views.py` 補上 |

有任何問題，把錯誤訊息和 Console／終端機畫面傳給前端。
