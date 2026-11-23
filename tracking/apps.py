from django.apps import AppConfig


class TrackingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tracking"
    verbose_name = "操作紀錄與意見回饋"
