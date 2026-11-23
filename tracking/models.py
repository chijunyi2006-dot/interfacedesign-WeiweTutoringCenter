"""操作紀錄（UIEvent）與意見回饋（Feedback）。欄位名稱與前端 tracker.js 送出的 JSON 完全一致。"""
from django.db import models


class UIEvent(models.Model):
    """前端 tracker.js 送來的一筆操作紀錄：誰（session）、何時、在哪頁、動了哪個元件。"""

    event_id = models.CharField("事件識別碼", max_length=64, unique=True)  # unique：同一筆重送不會重複寫入
    session_id = models.CharField("測試階段識別碼", max_length=64, db_index=True)
    seq = models.PositiveIntegerField("事件順序")
    event_type = models.CharField("事件種類", max_length=40, db_index=True)
    page_id = models.CharField("頁面代碼", max_length=100, db_index=True)
    target_id = models.CharField("元件代碼", max_length=200, blank=True, default="")
    occurred_at = models.DateTimeField("操作發生時間")
    ui_version = models.CharField("介面版本", max_length=20, blank=True, default="")
    test_phase = models.CharField("測試階段", max_length=40, blank=True, default="")
    data = models.JSONField("附加資料", default=dict, blank=True)
    created_at = models.DateTimeField("寫入時間", auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        verbose_name = "操作紀錄"
        verbose_name_plural = "操作紀錄"

    def __str__(self):
        return f"#{self.seq} {self.event_type} @ {self.page_id}/{self.target_id}"


class Feedback(models.Model):
    """使用者在頁面下方送出的按讚／倒讚與意見。"""

    RATING_CHOICES = [("like", "有幫助"), ("dislike", "沒幫助")]

    page_id = models.CharField("頁面代碼", max_length=100)
    rating = models.CharField("頁面評價", max_length=10, choices=RATING_CHOICES)
    comment = models.TextField("意見內容", max_length=2000)
    created_at = models.DateTimeField("送出時間", auto_now_add=True)

    class Meta:
        ordering = ["-id"]
        verbose_name = "意見回饋"
        verbose_name_plural = "意見回饋"

    def __str__(self):
        return f"{self.page_id} - {self.get_rating_display()}"
