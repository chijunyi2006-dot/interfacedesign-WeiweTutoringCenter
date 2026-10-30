// =========================================================
// 雲林偉文 Redesign － 共用互動功能（原生 JavaScript，以 defer 載入）
// 1. 手機漢堡選單、主要課程下拉選單
// 2. 多條件篩選（課程方案、師資、榜單共用同一套）
// 3. 對話框開關、未登入提示、分享、Toast
// =========================================================

const isLoggedIn = document.body.dataset.auth === "1";

// ---------- Toast 小提示 ----------
const toast = document.querySelector(".toast");
let toastTimer;
function showToast(message) {
  if (!toast) return;
  toast.textContent = message;
  toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { toast.hidden = true; }, 2200);
}

// ---------- 1. 導覽列 ----------
const nav = document.querySelector("#siteNav");
const menuToggle = document.querySelector(".menu-toggle");
const navClose = document.querySelector(".nav-close");
const backdrop = document.querySelector(".nav-backdrop");

function setMenu(open) {
  nav.classList.toggle("open", open);
  backdrop.hidden = !open;
  menuToggle.setAttribute("aria-expanded", String(open));
}
menuToggle.addEventListener("click", () => setMenu(true));

let resizeTimer;
window.addEventListener("resize", () => {
  nav.classList.add("no-transition");
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => nav.classList.remove("no-transition"), 300);
});
navClose.addEventListener("click", () => setMenu(false));
backdrop.addEventListener("click", () => setMenu(false));

document.querySelectorAll(".dropdown-toggle").forEach(button => {
  button.addEventListener("click", event => {
    event.stopPropagation();
    const dropdown = button.closest(".nav-dropdown");
    const open = dropdown.classList.toggle("open");
    button.setAttribute("aria-expanded", String(open));
  });
});
document.addEventListener("click", event => {
  document.querySelectorAll(".nav-dropdown.open").forEach(dropdown => {
    if (!dropdown.contains(event.target)) {
      dropdown.classList.remove("open");
      dropdown.querySelector(".dropdown-toggle").setAttribute("aria-expanded", "false");
    }
  });
});

// 標示目前所在頁面
document.querySelectorAll(".site-nav a.nav-link").forEach(link => {
  if (link.getAttribute("href").startsWith("#")) return;
  const url = new URL(link.href);
  if (url.pathname !== "/" && location.pathname.startsWith(url.pathname)) {
    link.setAttribute("aria-current", "page");
  }
});

// ---------- 2. 多條件篩選 ----------
// HTML 寫法：
//   <div data-filter-scope>
//     <input data-filter-keyword>                     → 關鍵字，比對卡片全部文字
//     <select data-filter="category">                 → 比對 .filter-item 的 data-category
//     <select data-filter="mode" data-match="contains"> → 部分比對（例如「實體面授 / 雲端隨選」包含「雲端」）
//     <b data-filter-count>                           → 顯示符合筆數
//     <p data-filter-empty hidden>                    → 無結果提示
//     <div class="filter-item" data-category="研究所">…</div>
//   </div>
document.querySelectorAll("[data-filter-scope]").forEach(scope => {
  const keywordInput = scope.querySelector("[data-filter-keyword]");
  const selects = [...scope.querySelectorAll("[data-filter]")];
  const items = [...scope.querySelectorAll(".filter-item")];
  const countEls = scope.querySelectorAll("[data-filter-count]");
  const honorEl = scope.querySelector("[data-filter-count-honor]");
  const uniqueEl = scope.querySelector("[data-filter-count-unique]");
  const emptyEl = scope.querySelector("[data-filter-empty]");
  const resetBtn = scope.querySelector("[data-filter-reset]");

  // 從網址參數預先帶入條件，例如 courses/?category=研究所
  const params = new URLSearchParams(location.search);
  selects.forEach(select => {
    const value = params.get(select.dataset.filter);
    if (value && [...select.options].some(option => option.value === value)) {
      select.value = value;
    }
  });
  if (keywordInput && params.get("q")) keywordInput.value = params.get("q");

  function applyFilter() {
    const keyword = keywordInput ? keywordInput.value.trim().toLowerCase() : "";
    let visible = [];

    items.forEach(item => {
      const matchKeyword = !keyword || item.textContent.toLowerCase().includes(keyword);
      const matchSelects = selects.every(select => {
        if (!select.value) return true;
        const itemValue = item.dataset[select.dataset.filter] || "";
        return select.dataset.match === "contains"
          ? itemValue.includes(select.value)
          : itemValue === select.value;
      });
      const show = matchKeyword && matchSelects;
      item.hidden = !show;
      if (show) visible.push(item);
    });

    countEls.forEach(el => { el.textContent = visible.length; });
    if (honorEl) honorEl.textContent = visible.filter(item => item.dataset.honor).length;
    if (uniqueEl) {
      const key = uniqueEl.dataset.filterCountUnique;
      uniqueEl.textContent = new Set(visible.map(item => item.dataset[key])).size;
    }
    if (emptyEl) emptyEl.hidden = items.length === 0 || visible.length > 0;
  }

  if (keywordInput) keywordInput.addEventListener("input", applyFilter);
  selects.forEach(select => select.addEventListener("change", applyFilter));
  if (resetBtn) {
    resetBtn.addEventListener("click", () => {
      if (keywordInput) keywordInput.value = "";
      selects.forEach(select => { select.value = ""; });
      applyFilter();
    });
  }
  applyFilter();
});

// ---------- 3. 對話框 ----------
document.addEventListener("click", event => {
  const opener = event.target.closest("[data-dialog-open]");
  if (opener) {
    document.getElementById(opener.dataset.dialogOpen)?.showModal();
    return;
  }
  const closer = event.target.closest("[data-dialog-close]");
  if (closer) {
    closer.closest("dialog")?.close();
    return;
  }
  // 點對話框外側（backdrop）關閉
  if (event.target.tagName === "DIALOG") event.target.close();
});

// 網址帶 #對話框id 時自動打開，例如 /contact/#lineDialog
function openDialogFromHash() {
  const dialog = location.hash && document.getElementById(location.hash.slice(1));
  if (dialog && dialog.tagName === "DIALOG" && !dialog.open) dialog.showModal();
}
openDialogFromHash();
window.addEventListener("hashchange", openDialogFromHash);

// 對話框關閉時暫停影片（重設 iframe src）
document.querySelectorAll("dialog").forEach(dialog => {
  dialog.addEventListener("close", () => {
    dialog.querySelectorAll("iframe").forEach(frame => { frame.src = frame.src; });
  });
});

// 未登入時點到會員功能 → 跳出登入提示
const loginDialog = document.querySelector("#loginDialog");
document.querySelectorAll("[data-requires-login]").forEach(button => {
  button.addEventListener("click", event => {
    if (isLoggedIn) return;
    event.preventDefault();
    button.closest("dialog")?.close();
    loginDialog.showModal();
  });
});

// 尚未設定網址的連結（例如 LINE 官方帳號）：提示而不是跳到頁首
document.querySelectorAll('a[aria-disabled="true"]').forEach(link => {
  link.addEventListener("click", event => {
    event.preventDefault();
    showToast("此為專題示意帳號，尚未連結真實 LINE");
  });
});

// 聯絡我們：切換據點地圖（斗六 / 虎尾）
const mapFrame = document.querySelector("#mapFrame");
const mapLink = document.querySelector("#mapLink");
document.querySelectorAll(".map-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    const address = encodeURIComponent(tab.dataset.address);
    const place = encodeURIComponent(tab.dataset.place);
    mapFrame.src = `https://www.google.com/maps?q=${address}&hl=zh-TW&z=16&output=embed`;
    mapLink.href = `https://www.google.com/maps/search/?api=1&query=${place}`;
    document.querySelectorAll(".map-tab").forEach(other => {
      other.classList.toggle("active", other === tab);
      other.setAttribute("aria-selected", String(other === tab));
    });
  });
});

// ---------- 師資比較（作業一 Flow 2：最多 3 位並列） ----------
const compareBar = document.querySelector("[data-compare-bar]");
if (compareBar) {
  const MAX_COMPARE = 3;
  let selected = [];
  const cardOf = id => document.querySelector(`[data-compare-card="${id}"]`);

  function renderCompare() {
    document.querySelectorAll("[data-compare-toggle]").forEach(button => {
      const on = selected.includes(button.dataset.compareToggle);
      button.setAttribute("aria-pressed", String(on));
      button.textContent = on ? "已加入比較" : "＋ 加入比較";
    });
    compareBar.querySelector("[data-compare-count]").textContent = selected.length;
    const chips = compareBar.querySelector("[data-compare-chips]");
    chips.replaceChildren(...selected.map(id => {
      const chip = document.createElement("span");
      chip.textContent = cardOf(id).dataset.compareName;
      return chip;
    }));
    compareBar.hidden = selected.length === 0;
    document.body.classList.toggle("has-compare", selected.length > 0);
  }

  document.querySelectorAll("[data-compare-toggle]").forEach(button => {
    button.addEventListener("click", () => {
      const id = button.dataset.compareToggle;
      if (selected.includes(id)) {
        selected = selected.filter(other => other !== id);
      } else if (selected.length >= MAX_COMPARE) {
        showToast(`最多比較 ${MAX_COMPARE} 位老師，請先移除一位`);
        return;
      } else {
        selected.push(id);
      }
      renderCompare();
    });
  });

  compareBar.querySelector("[data-compare-clear]").addEventListener("click", () => {
    selected = [];
    renderCompare();
  });

  // 比較表：用 textContent 建立內容，避免資料中的文字被當成 HTML
  compareBar.querySelector("[data-compare-open]").addEventListener("click", () => {
    if (selected.length < 2) {
      showToast("請至少選 2 位老師再比較");
      return;
    }
    const cards = selected.map(cardOf).map(card => card.dataset);
    const rows = [
      ["授課科目", "compareSubject"],
      ["學經歷", "compareEducation"],
      ["學生評價", "compareRating", " / 5.0"],
      ["上榜學生", "compareSuccess", " 位"],
      ["教學特色", "compareTagline"],
    ];
    const table = document.querySelector("[data-compare-table]");
    const head = document.createElement("thead");
    const headRow = head.insertRow();
    headRow.appendChild(document.createElement("th"));
    cards.forEach(data => {
      const th = document.createElement("th");
      th.textContent = data.compareName;
      headRow.appendChild(th);
    });
    const body = document.createElement("tbody");
    rows.forEach(([label, key, unit = ""]) => {
      const row = body.insertRow();
      const th = document.createElement("th");
      th.textContent = label;
      row.appendChild(th);
      // 評價與上榜數最高者標示顏色
      const numbers = cards.map(data => parseFloat(data[key]));
      const best = unit ? Math.max(...numbers) : null;
      cards.forEach(data => {
        const cell = row.insertCell();
        cell.textContent = data[key] + unit;
        if (best !== null && parseFloat(data[key]) === best) cell.className = "best";
      });
    });
    table.replaceChildren(head, body);
    document.querySelector("#compareDialog").showModal();
  });
}

// 分享：手機用系統分享，電腦則複製網址
document.querySelectorAll("[data-share]").forEach(button => {
  button.addEventListener("click", async () => {
    const shareData = { title: document.title, url: location.href };
    try {
      if (navigator.share) {
        await navigator.share(shareData);
      } else {
        await navigator.clipboard.writeText(location.href);
        showToast("已複製課程連結，可貼給家人或同學");
      }
    } catch (error) {
      // 使用者取消分享時不需處理
    }
  });
});
