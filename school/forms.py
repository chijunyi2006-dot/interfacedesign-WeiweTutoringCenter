"""建議的 forms.py：聯絡我們表單（欄位名稱與 templates/contact.html 一致）"""
from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    # 同意條款只用來驗證，不存進資料庫
    agree = forms.BooleanField(error_messages={"required": "請勾選同意後再送出"})
    phone = forms.RegexField(regex=r"^[0-9\-+() ]{8,20}$", error_messages={"invalid": "請輸入正確的電話號碼"})

    class Meta:
        model = ContactMessage
        fields = ["name", "phone", "identity", "campus", "category", "contact_time",
                  "school_info", "message", "line_id"]
