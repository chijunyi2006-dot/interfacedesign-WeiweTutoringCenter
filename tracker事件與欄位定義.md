# Tracker 事件與欄位定義（前端，Week10 偵測＋Week11 上傳）

> 前端負責：蔡以琳｜程式：`static/js/tracker.js`
> 一筆紀錄 ＝ 一張字條，寫著「誰、在哪一頁、動了哪個元件、做了什麼、什麼時候」。

---

## 1. 一筆紀錄長什麼樣子

```json
{
  "event_id": "b3c1…",
  "session_id": "7f2a…",
  "seq": 2,
  "event_type": "filter_change",
  "page_id": "courses",
  "target_id": "filter_category",
  "occurred_at": "2026-11-16T05:20:31.000Z",
  "ui_version": "v1",
  "test_phase": "week11",
  "data": { "result_count": 4, "filter_name": "category", "selected_value": "研究所" }
}
```

讀成一句話：「在課程頁，把『類別』下拉選單改成『研究所』，畫面剩 4 筆。」

## 2. 每個欄位的定義

| 欄位 | 型別 | 意思 | 例子 | 備註 |
|---|---|---|---|---|
| `event_id` | 字串 | 這一筆的唯一編號 | `b3c1…` | 不會重複，之後存資料庫用來避免重複寫入 |
| `session_id` | 字串 | 這「一次測試」的編號 | `7f2a…` | 同一次測試的所有紀錄都一樣；按「清除紀錄」才換新的 |
| `seq` | 整數 | 這次測試的第幾筆 | `2` | 從 1 開始遞增，用來還原先後順序 |
| `event_type` | 字串 | 做了什麼事（事件種類） | `filter_change` | 種類見第 3 節 |
| `page_id` | 字串 | 事件發生在哪一頁 | `courses` | 由網址推出，見第 4 節 |
| `target_id` | 字串 | 動到哪個元件 | `filter_category` | 同一種事件靠它分辨是哪個元件；可為空字串 |
| `occurred_at` | 字串 | 事件發生的時間 | `2026-11-16T05:20:31.000Z` | ISO 格式，UTC 時間（台灣＋8 小時） |
| `ui_version` | 字串 | 網站介面版本 | `v1` | 改版後改成 `v2`，才能比較新舊 |
| `test_phase` | 字串 | 測試階段 | `week11` | 區分不同次測試（常數在 tracker.js 最上方 `TEST_PHASE`） |
| `data` | 物件 | 補充細節 | `{"result_count":4}` | 只允許第 5 節的白名單欄位，沒有補充就是 `{}` |

## 3. 事件名稱（event_type）

| 事件名稱 | 意思 | 什麼時候記錄 | target_id 的例子 | data 裡有什麼 |
|---|---|---|---|---|
| `page_view` | 進入某一頁 | 按「開始測試」時；或測試中載入新頁面時 | `page` | 無 |
| `page_duration` | 這一頁看了多久 | 離開頁面、切到別的分頁、按停止或匯出時 | `page` | `visible_ms`、`reason` |
| `nav_click` | 點了連結（換頁） | 點導覽列、頁尾、首頁卡片等連結 | `nav_teachers`、`nav_brand`、`link_courses_2` | 無 |
| `button_click` | 點了按鈕 | 點開對話框、分享、加入比較、清除條件、地圖分頁、匯出等 | `open_dialog`、`filter_reset`、`share`、`export_json` | 開對話框時有 `dialog` |
| `search` | 在搜尋框輸入 | **停止輸入 0.5 秒後**才記一筆（不是每打一個字） | `courseKeyword` | `keyword_length`、`result_count` |
| `filter_change` | 換了下拉篩選條件 | 改變類別、科系、上課方式、年度等選單；榜單頁切換圖表形式 | `filter_category`、`filter_department`、`filter_mode`、`filter_year`、`rank_chart_type` | `filter_name`、`selected_value`、`result_count` |
| `form_invalid` | 表單欄位沒通過檢查 | 送出時某欄位未填或格式錯 | 表單 id（沒有就是 `form`） | `field`、`reason` |
| `form_validated` | 表單前端檢查通過 | 送出且全部欄位通過瀏覽器檢查 | 表單 id（沒有就是 `form`） | 無 |
| `feedback_submit` | 意見回饋送出成功 | 頁尾意見回饋表單被後端接受之後 | `feedback-form` | `rating`（like／dislike，**不存意見文字**） |

> 登出按鈕的表單不記錄；測試工具列自己的按鈕（開始、停止、查看、清除）也不記錄。

### target_id 命名規則

| 類型 | 規則 | 例子 |
|---|---|---|
| 導覽列連結 | `nav_` ＋ 網址路徑；有類別或科系再接上去 | `/teachers/` → `nav_teachers`；`/courses/?category=研究所` → `nav_courses_研究所` |
| 內容區連結 | `link_` ＋ 網址路徑 | `/courses/2/` → `link_courses_2` |
| 下拉篩選 | `filter_` ＋ 篩選名稱 | `filter_category` |
| 搜尋框 | 該搜尋框的 id；沒有就是 `keyword` | `courseKeyword`、`teacherKeyword`、`rankKeyword`、`syllabusKeyword`（課程詳情頁） |
| 表單驗證練習 | 表單 id | 課程頁的 `inquiryDemoForm`（`form_invalid`／`form_validated`，`field` 為 `demoEmail`） |

## 4. 頁面代碼（page_id）

由網址自動推出，不需要手動設定：

| 網址 | page_id |
|---|---|
| `/` | `home` |
| `/courses/` | `courses` |
| `/courses/3/` | `courses_detail` |
| `/teachers/` | `teachers` |
| `/rankings/` 或 `/ranking/` | `rankings`（兩種網址都統一成 rankings） |
| `/contact/` | `contact` |
| `/login/` | `login` |
| `/member/` | `member` |

## 5. data 的欄位（白名單）

只有這些欄位會被保存，其他一律丟掉。

| 欄位 | 意思 | 單位／值 | 用在哪些事件 |
|---|---|---|---|
| `result_count` | 篩選或搜尋後，畫面上剩幾筆 | 整數 | `search`、`filter_change` |
| `keyword_length` | 搜尋文字的長度 | 字數（**不存文字本身**） | `search` |
| `filter_name` | 改的是哪個篩選條件 | `category`、`department`、`mode`、`year`；榜單圖表形式為 `chart_type`（值 `bar`／`line`） | `filter_change` |
| `selected_value` | 選了哪個值 | 例如 `研究所`；選「全部」記 `all` | `filter_change` |
| `visible_ms` | 這一段頁面「看得到」的時間 | **毫秒**（10000 ＝ 10 秒） | `page_duration` |
| `reason` | 為什麼結算這一筆 | 見下表 | `page_duration`、`form_invalid` |
| `dialog` | 開啟的是哪個對話框 | 例如 `lineDialog` | `button_click` |
| `field` | 哪個表單欄位出錯 | 欄位 name | `form_invalid` |
| `rating` | 回饋評價 | `like`（有幫助）、`dislike`（沒幫助） | `feedback_submit` |

`reason` 的值：

| 事件 | reason | 意思 |
|---|---|---|
| `page_duration` | `pagehide` | 離開這一頁（換頁、關分頁） |
| | `hidden` | 切到別的分頁或視窗，頁面看不到了 |
| | `stop` | 按了「停止紀錄」 |
| | `export` | 按了「匯出 JSON」前先結算 |
| `form_invalid` | `value_missing` | 必填沒填 |
| | `type_mismatch` | 格式不對（例如 Email 格式） |
| | `pattern_mismatch` | 不符合規定的格式（例如電話） |
| | `invalid` | 其他原因 |

## 6. 隱私規則

- **不存**：搜尋文字原文、姓名、電話、Email、LINE ID、密碼、表單內容。
- 只存「長度」「筆數」「選了哪個選項」這類不能還原個資的資訊。
- 預設不記錄，按「開始測試」才開始；按「停止紀錄」就停。
- 本機暫存在 `sessionStorage`（只在同一個分頁裡，關掉分頁就消失）。
- 按「開始測試」後，每一筆紀錄會同時 POST 到 `/api/events/` 存進資料庫；上傳失敗只會在 Console 顯示警告，不影響網站，本機暫存的紀錄還在。
- 意見回饋的**文字內容**會存進 `Feedback` 資料表（使用者主動填寫），但**不會**寫進操作紀錄。

## 7. 可以在 Console 使用的指令

| 指令 | 做什麼 |
|---|---|
| `UITracker.start()` | 開始記錄 |
| `UITracker.stop()` | 停止記錄 |
| `UITracker.isEnabled()` | 現在有沒有在記錄（`true`／`false`） |
| `UITracker.read()` | 取得全部紀錄 |
| `console.table(UITracker.read())` | 用表格查看紀錄 |
| `UITracker.reset()` | 清除全部紀錄 |
| `UITracker.exportJSON()` | 下載成 `week10_events.json` |
| `UITracker.track("事件", "元件代碼")` | 手動新增一筆（測試用） |

## 8. 與後端約定

- 收件口：`POST /api/events/`（操作紀錄）、`POST /api/feedback/`（意見回饋）。
- `UIEvent` 資料表欄位與第 2 節一致，另加 `created_at`（資料庫寫入時間，自動產生）。
- 必填：`event_id`、`session_id`、`seq`、`event_type`、`page_id`、`occurred_at`；其餘可為空。
- 詳細規格、驗收步驟見《後端交接說明_Week11行為紀錄與意見回饋.md》。
