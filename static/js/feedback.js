// =========================================================
// feedback.js － 意見回饋表單（Week11）
// 把「有幫助／沒幫助」與意見，用 fetch 以 JSON 送到 /api/feedback/（Django 存進 Feedback 資料表）。
// 流程：檢查必填 → 帶 CSRF token 送出 → 成功才清空表單、失敗保留輸入 → 顯示結果與回饋編號。
// 這支只負責「意見」；操作紀錄仍由 tracker.js 負責。
// =========================================================
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("feedback-form");
  if (!form) return;
  const button = document.getElementById("feedback-submit");
  const message = document.getElementById("feedback-message");
  let sending = false;

  // 頁面代碼：與 tracker.js 相同規則（網址第一段；榜單統一成 rankings；詳情頁加 _detail）
  function currentPageId() {
    const path = location.pathname.replace(/^\/|\/$/g, "");
    if (!path) return "home";
    const parts = path.split("/");
    const name = parts[0] === "ranking" ? "rankings" : parts[0];
    return parts.length > 1 ? name + "_detail" : name;
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    if (sending) return;

    const rating = form.querySelector('input[name="rating"]:checked');
    const comment = form.elements.comment.value.trim();
    if (!rating) { message.textContent = "請先選擇「有幫助」或「沒幫助」。"; return; }
    if (!comment) { message.textContent = "請填寫意見。"; form.elements.comment.focus(); return; }

    const token = form.querySelector('[name="csrfmiddlewaretoken"]').value;

    sending = true;                       // 送出中：停用按鈕，避免連按送出兩次
    button.disabled = true;
    message.textContent = "送出中…";

    try {
      const response = await fetch(form.dataset.apiUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json", "X-CSRFToken": token },
        body: JSON.stringify({ page_id: currentPageId(), rating: rating.value, comment: comment }),
      });
      if (response.status === 403) throw new Error("驗證失敗，請重新整理頁面再試。");

      const result = await response.json();
      if (!response.ok || !result.success) throw new Error(result.message || "送出失敗，請稍後再試。");

      message.textContent = result.message + " 回饋編號：" + result.id;
      form.reset();                       // 成功才清空；失敗會保留使用者輸入
      if (window.UITracker) UITracker.track("feedback_submit", "feedback-form", { rating: rating.value });
    } catch (error) {
      message.textContent = "未能確認送出成功：" + error.message;
    } finally {
      sending = false;
      button.disabled = false;
    }
  });
});
