"""後台：查看操作紀錄與意見回饋（唯讀為主，避免誤改研究資料）。"""
from django.contrib import admin

from .models import Feedback, UIEvent


@admin.register(UIEvent)
class UIEventAdmin(admin.ModelAdmin):
    list_display = ("id", "session_id", "seq", "event_type", "page_id", "target_id", "occurred_at", "ui_version", "test_phase")
    list_filter = ("event_type", "page_id", "ui_version", "test_phase")
    search_fields = ("session_id", "target_id", "event_id")
    ordering = ("-id",)
    readonly_fields = [field.name for field in UIEvent._meta.fields]

    def has_add_permission(self, request):
        return False


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "page_id", "rating", "short_comment", "created_at")
    list_filter = ("rating", "page_id")
    search_fields = ("comment",)
    readonly_fields = ("page_id", "rating", "comment", "created_at")

    @admin.display(description="意見")
    def short_comment(self, obj):
        return obj.comment[:40]

    def has_add_permission(self, request):
        return False
