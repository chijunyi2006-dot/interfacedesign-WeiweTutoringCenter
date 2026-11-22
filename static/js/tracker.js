// =========================================================
// tracker.js － 操作紀錄員（Week10：先把操作變成「可讀的紀錄」）
//
// 一句話：使用者在網站上做了什麼，就寫一張小字條，暫存在瀏覽器裡。
//
// 一張字條（事件）長這樣：
//   event_type  做了什麼？      例：nav_click（點導覽列）
//   page_id     在哪一頁？      例：courses
//   target_id   動到哪個元件？  例：nav_teachers
//   occurred_at 什麼時候？
//   seq         第幾筆？（同一次測試內的順序）
//   data        補充資料        例：{ result_count: 3 }
//
// 規則（保護使用者）：
//   1. 預設「停用」，按了「開始測試」才會記。
//   2. 只存白名單欄位；不存搜尋原文、Email、電話、密碼。
//   3. 存在 sessionStorage（同一個分頁），關掉分頁就消失；此階段不上傳。
//   4. 任何錯誤都不能影響網站原本的功能。
// =========================================================
(function () {
  "use strict";

  const KEY_ENABLED = "ui_tracker_enabled";
  const KEY_EVENTS = "ui_tracker_events";
  const KEY_SESSION = "ui_tracker_session";
  const KEY_SEQ = "ui_tracker_seq";
  const UI_VERSION = "v1";
  const TEST_PHASE = "week11";

  // Week11：把每一筆紀錄送到後端的收件口（Django：tracking/urls.py 的 receive_event）
  const API_URL = "/api/events/";

  // data 裡只允許這些欄位被保存（白名單）
  const ALLOWED_FIELDS = [
    "result_count", "keyword_length", "filter_name", "selected_value",
    "visible_ms", "reason", "dialog", "field", "rating",
  ];

  // ---------- 安全的 sessionStorage（失敗時不影響網站） ----------
  function readStore(key, fallback) {
    try {
      const raw = sessionStorage.getItem(key);
      return raw === null ? fallback : JSON.parse(raw);
    } catch (error) {
      return fallback;
    }
  }
  function writeStore(key, value) {
    try {
      sessionStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (error) {
      return false;
    }
  }

  function makeId() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    return "id-" + Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
  }

  function sessionId() {
    let id = readStore(KEY_SESSION, "");
    if (!id) {
      id = makeId();
      writeStore(KEY_SESSION, id);
    }
    return id;
  }

  // 目前在哪一頁：用網址推出代碼，例如 /teachers/ → teachers
  function pageId() {
    const path = location.pathname.replace(/^\/|\/$/g, "");
    if (!path) return "home";
    const parts = path.split("/");
    // 後端的榜單網址是 /ranking/，前端文件寫 /rankings/，統一成 rankings，統計時才不會分成兩種
    const name = parts[0] === "ranking" ? "rankings" : parts[0];
    return parts.length > 1 ? name + "_detail" : name;
  }

  // ---------- Week11：傳送到後端 ----------
  // Django 會擋掉沒有 CSRF token 的 POST，所以先從 cookie 取 token（base.html 的 {% csrf_token %} 會讓 Django 設好 cookie）
  function getCSRFToken() {
    const cookies = document.cookie.split(";");
    for (const cookie of cookies) {
      const value = cookie.trim();
      if (value.startsWith("csrftoken=")) return decodeURIComponent(value.substring("csrftoken=".length));
    }
    const field = document.querySelector('#trackerBar [name="csrfmiddlewaretoken"]');
    return field ? field.value : "";
  }

  const upload = { ok: 0, failed: 0 };   // 這一頁送出的結果，顯示在測試面板上

  async function sendEvent(event) {
    const token = getCSRFToken();
    if (!token) {
      console.warn("找不到 CSRF Token，暫不傳送");
      upload.failed += 1;
      updateBar();
      return false;
    }
    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": token },
        body: JSON.stringify(event),
        credentials: "same-origin",
        keepalive: true,            // 離開頁面時送出的最後一筆（page_duration）也能送完
      });
      if (!response.ok) {
        console.warn("操作紀錄上傳失敗：", response.status);
        upload.failed += 1;
        updateBar();
        return false;
      }
      upload.ok += 1;
      updateBar();
      return true;
    } catch (error) {
      console.warn("API 連線失敗：", error);   // 失敗也不影響網站；本機暫存的紀錄還在
      upload.failed += 1;
      updateBar();
      return false;
    }
  }

  function cleanData(data) {
    const result = {};
    if (!data) return result;
    ALLOWED_FIELDS.forEach(name => {
      if (data[name] === undefined || data[name] === null) return;
      const value = data[name];
      result[name] = typeof value === "string" ? value.slice(0, 60) : value;
    });
    return result;
  }

  // ---------- 控制 ----------
  function isEnabled() {
    return readStore(KEY_ENABLED, false) === true;
  }

  function start() {
    const wasEnabled = isEnabled();
    writeStore(KEY_ENABLED, true);
    if (!wasEnabled) {            // 只有「停用 → 啟用」才記一次 page_view，重複按開始不會重複記
      track("page_view", "page");
      startVisibleTimer();
    }
    updateBar();
  }

  function stop() {
    if (!isEnabled()) return;
    flushVisibleTime("stop");     // 停止前先結算這一段可見時間
    writeStore(KEY_ENABLED, false);
    visibleStartedAt = null;
    updateBar();
  }

  // ---------- 記錄 ----------
  function track(eventType, targetId, data) {
    if (!isEnabled()) return null;
    try {
      const seq = readStore(KEY_SEQ, 0) + 1;
      const event = {
        event_id: makeId(),
        session_id: sessionId(),
        seq: seq,
        event_type: eventType,
        page_id: pageId(),
        target_id: targetId || "",
        occurred_at: new Date().toISOString(),
        ui_version: UI_VERSION,
        test_phase: TEST_PHASE,
        data: cleanData(data),
      };
      const events = readStore(KEY_EVENTS, []);
      events.push(event);
      writeStore(KEY_EVENTS, events);
      writeStore(KEY_SEQ, seq);
      console.log("已記錄事件：", event);
      sendEvent(event);             // 每筆事件只送一次；送不送得成功都不影響原網站
      updateBar();
      return event;
    } catch (error) {
      return null;                // 紀錄失敗絕不影響原網站
    }
  }

  function read() {
    return readStore(KEY_EVENTS, []);
  }

  function reset() {
    try {
      sessionStorage.removeItem(KEY_EVENTS);
      sessionStorage.removeItem(KEY_SEQ);
      sessionStorage.removeItem(KEY_SESSION);
    } catch (error) { /* 忽略 */ }
    updateBar();
  }

  function exportJSON() {
    flushVisibleTime("export");   // 匯出前先結算；仍啟用就繼續計時
    if (isEnabled()) startVisibleTimer();
    const blob = new Blob([JSON.stringify(read(), null, 2)], { type: "application/json" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "week10_events.json";
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  }

  // ---------- 頁面可見時間（只累計「看得到頁面」的時間） ----------
  let visibleStartedAt = null;

  function startVisibleTimer() {
    if (isEnabled() && document.visibilityState === "visible" && visibleStartedAt === null) {
      visibleStartedAt = performance.now();
    }
  }

  function flushVisibleTime(reason) {
    if (visibleStartedAt === null) return;
    const ms = Math.round(performance.now() - visibleStartedAt);
    visibleStartedAt = null;      // 先清空起點，避免同一段被算兩次
    if (ms > 0) track("page_duration", "page", { visible_ms: ms, reason: reason });
  }

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") flushVisibleTime("hidden");
    else startVisibleTimer();
  });
  window.addEventListener("pagehide", () => flushVisibleTime("pagehide"));
  window.addEventListener("pageshow", event => {
    // 從「上一頁」回來時瀏覽器可能直接還原舊畫面，要重新計時並再記一次進入
    if (event.persisted && isEnabled()) {
      track("page_view", "page");
      startVisibleTimer();
    }
  });

  // =========================================================
  // 偵測：把網站上的操作接到 track()
  // 用「事件委派」：只在 document 上聽一次，不需要改每個按鈕，
  // 也不會干擾 script.js 原本的功能（原功能先執行，這裡再記錄）。
  // =========================================================

  // 導覽列連結：用網址推出代碼，例如 /teachers/ → nav_teachers
  function navTargetId(link) {
    const url = new URL(link.href, location.href);
    const path = url.pathname.replace(/^\/|\/$/g, "") || "home";
    let id = "nav_" + path.replace(/\//g, "_");
    const category = url.searchParams.get("category");
    const department = url.searchParams.get("department");
    if (category) id += "_" + category;
    if (department) id += "_" + department;
    return id;
  }

  document.addEventListener("click", event => {
    if (!isEnabled()) return;

    // 1. 導覽列、頁尾連結 → nav_click
    const navLink = event.target.closest(".site-nav a, .brand, .site-footer a[href]");
    if (navLink && navLink.getAttribute("href") && !navLink.getAttribute("href").startsWith("#")) {
      track("nav_click", navLink.classList.contains("brand") ? "nav_brand" : navTargetId(navLink));
      return;
    }

    // 2. 內容區的卡片連結（首頁身分入口、課程卡、老師卡…）→ nav_click
    const cardLink = event.target.closest("main a[href]");
    if (cardLink && !cardLink.getAttribute("href").startsWith("#") && !cardLink.target) {
      track("nav_click", "link_" + navTargetId(cardLink).replace(/^nav_/, ""));
      return;
    }

    // 3. 按鈕 → button_click（開啟對話框、分享、加入比較、清除條件…）
    const button = event.target.closest("button, [data-dialog-open]");
    if (!button || button.closest("#trackerBar")) return;   // 測試工具列本身不記
    let target = button.id || "";
    const data = {};
    if (button.dataset.dialogOpen) { target = "open_dialog"; data.dialog = button.dataset.dialogOpen; }
    else if (button.dataset.share !== undefined) target = "share";
    else if (button.dataset.compareToggle !== undefined) target = "compare_toggle";
    else if (button.dataset.compareOpen !== undefined) target = "compare_open";
    else if (button.dataset.filterReset !== undefined) target = "filter_reset";
    else if (button.classList.contains("map-tab")) target = "map_tab";
    else if (button.classList.contains("dropdown-toggle")) target = "nav_dropdown";
    else if (button.classList.contains("menu-toggle")) target = "menu_toggle";
    else if (!target) target = "button";
    track("button_click", target, data);
  });

  // 搜尋框：畫面照常即時更新，紀錄等「停止輸入 500 毫秒」才留下（不存搜尋原文）
  const searchTimers = new WeakMap();
  let composing = false;
  document.addEventListener("compositionstart", () => { composing = true; });
  document.addEventListener("compositionend", () => { composing = false; });

  function resultCountOf(element) {
    const scope = element.closest("[data-filter-scope]");
    const counter = scope && scope.querySelector("[data-filter-count]");
    return counter ? parseInt(counter.textContent, 10) : undefined;
  }

  document.addEventListener("input", event => {
    const input = event.target;
    if (!input.matches || !input.matches("[data-filter-keyword]")) return;
    clearTimeout(searchTimers.get(input));
    searchTimers.set(input, setTimeout(() => {
      if (composing) return;      // 中文還在組字，不記
      track("search", input.id || "keyword", {
        keyword_length: input.value.trim().length,
        result_count: resultCountOf(input),
      });
    }, 500));
  });

  // 下拉篩選 → filter_change（記錄選了什麼、剩幾筆）
  document.addEventListener("change", event => {
    const select = event.target;
    if (!select.matches || !select.matches("select[data-filter]")) return;
    track("filter_change", "filter_" + select.dataset.filter, {
      filter_name: select.dataset.filter,
      selected_value: select.value || "all",
      result_count: resultCountOf(select),
    });
  });

  // 表單：原生驗證失敗 → form_invalid（只記欄位與原因，不記內容）
  document.addEventListener("invalid", event => {
    const field = event.target;
    const v = field.validity || {};
    const reason = v.valueMissing ? "value_missing"
      : v.typeMismatch ? "type_mismatch"
      : v.patternMismatch ? "pattern_mismatch"
      : "invalid";
    track("form_invalid", (field.form && field.form.id) || "form", {
      field: field.name || field.id || "field",
      reason: reason,
    });
  }, true);

  // submit 只有在原生驗證都通過時才會觸發 → form_validated（登出表單不算）
  document.addEventListener("submit", event => {
    const form = event.target;
    if (form.closest && form.closest(".nav-logout")) return;
    if (form.id === "feedback-form") return;   // 意見回饋有自己的檢查，成功時由 feedback.js 記 feedback_submit
    track("form_validated", form.id || "form");
  });

  // =========================================================
  // 測試工具列（base.html 的 #trackerBar）：開始／停止／查看／匯出／清除
  // =========================================================
  function updateBar() {
    const bar = document.getElementById("trackerBar");
    if (!bar) return;
    const on = isEnabled();
    bar.dataset.state = on ? "on" : "off";
    const status = bar.querySelector("[data-tracker-status]");
    const count = bar.querySelector("[data-tracker-count]");
    if (status) status.textContent = on ? "記錄中" : "未記錄";
    if (count) count.textContent = read().length;
    const sent = bar.querySelector("[data-tracker-upload]");
    if (sent) sent.textContent = "本頁上傳：成功 " + upload.ok + "／失敗 " + upload.failed;
  }

  function bindBar() {
    const bar = document.getElementById("trackerBar");
    if (!bar) return;
    bar.addEventListener("click", event => {
      const action = event.target.closest("[data-tracker-action]");
      if (!action) return;
      const name = action.dataset.trackerAction;
      if (name === "start") start();
      else if (name === "stop") stop();
      else if (name === "view") { console.table(read()); showToastSafe("已在 Console 顯示紀錄"); }
      else if (name === "export") {
        if (isEnabled()) track("button_click", "export_json");   // 先記「按了匯出」，下載檔才包含這一筆
        exportJSON();
      }
      else if (name === "reset") reset();
    });
    updateBar();
  }

  function showToastSafe(message) {
    if (typeof showToast === "function") showToast(message);
  }

  // 公開給 Console 與其他程式使用
  window.UITracker = { start, stop, isEnabled, track, read, reset, exportJSON };

  // 頁面載入：若上一頁已經在記錄，這一頁要記「進入」並繼續計時
  function init() {
    bindBar();
    if (isEnabled()) {
      track("page_view", "page");
      startVisibleTimer();
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
