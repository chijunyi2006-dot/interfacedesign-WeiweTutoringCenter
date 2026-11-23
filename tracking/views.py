"""
接收前端資料的兩個 API（都只收 POST、都要 CSRF token）：
  POST /api/events/    ← static/js/tracker.js 每記一筆就送一筆
  POST /api/feedback/  ← static/js/feedback.js 送出意見回饋
成功回 {"success": true, "id": 紀錄編號}；失敗回 {"success": false, "message": 原因} 與 400。
"""
import json

from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

from .models import Feedback, UIEvent

REQUIRED_EVENT_FIELDS = ["event_id", "session_id", "seq", "event_type", "page_id", "occurred_at"]
# data 白名單（與 tracker.js 的 ALLOWED_FIELDS、《tracker事件與欄位定義.md》第 5 節一致）。
# 後端再過濾一次：就算有人繞過前端直接 POST，也不會把姓名、電話等多餘欄位存進資料庫。
DATA_FIELDS = {"result_count", "keyword_length", "filter_name", "selected_value",
               "visible_ms", "reason", "dialog", "field", "rating"}
MAX_DATA_TEXT = 60           # 字串值最多 60 字（與前端 cleanData 相同）
MAX_SEQ = 2_147_483_647      # PostgreSQL integer 上限，超過會讓 Neon 回 500
FEEDBACK_PAGES = {"home", "courses", "courses_detail", "teachers", "rankings", "contact", "member", "login"}
MAX_EVENT_BYTES = 10_000     # 一筆事件只有幾百 bytes，擋掉異常大的請求
MAX_FEEDBACK_BYTES = 30_000  # 意見最多 2000 字；中文在 JSON 裡最多 6 bytes/字，留足空間


def _error(message, status=400):
    return JsonResponse({"success": False, "message": message}, status=status)


def _parse_json_object(request, limit):
    """回傳 (dict, None) 或 (None, 錯誤回應)。"""
    if len(request.body) > limit:
        return None, _error("資料過大", 413)
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, _error("JSON 格式錯誤")
    if not isinstance(payload, dict):
        return None, _error("資料格式錯誤")
    return payload, None


def _text(value, limit):
    """轉成字串、去掉 PostgreSQL 不接受的 NUL 字元，再截到欄位長度。"""
    return str(value).replace("\x00", "").strip()[:limit]


def _clean_data(data):
    """只留白名單欄位；值只接受字串、整數、小數、布林，其餘（巢狀物件、陣列）丟掉。"""
    cleaned = {}
    for key, value in data.items():
        if key not in DATA_FIELDS or value is None:
            continue
        if isinstance(value, str):
            cleaned[key] = _text(value, MAX_DATA_TEXT)
        elif isinstance(value, (bool, int, float)):
            cleaned[key] = value
    return cleaned


@require_POST
@csrf_protect
def receive_event(request):
    payload, error = _parse_json_object(request, MAX_EVENT_BYTES)
    if error:
        return error

    missing = [name for name in REQUIRED_EVENT_FIELDS
               if payload.get(name) is None or _text(payload[name], 1000) == ""]
    if missing:
        return _error("缺少必要欄位：" + "、".join(missing))

    try:
        occurred_at = parse_datetime(str(payload["occurred_at"]))
    except ValueError:  # 格式像 ISO 但日期不存在，例如 2026-13-40
        occurred_at = None
    if occurred_at is None or occurred_at.tzinfo is None:
        return _error("occurred_at 必須是含時區的 ISO 時間")

    seq = payload["seq"]
    if isinstance(seq, str) and seq.strip().isdigit():  # 容許 "2" 這種字串數字
        seq = int(seq)
    if isinstance(seq, bool) or not isinstance(seq, int) or not 0 <= seq <= MAX_SEQ:
        return _error("seq 必須是 0 以上的整數")

    data = payload.get("data")
    if data is None:
        data = {}
    if not isinstance(data, dict):
        return _error("data 必須是 JSON 物件")
    data = _clean_data(data)

    event_id = _text(payload["event_id"], 64)
    existing = UIEvent.objects.filter(event_id=event_id).first()
    if existing:  # 前端重送同一筆：視為成功，不重複寫入
        return JsonResponse({"success": True, "message": "事件已存在", "id": existing.id})

    try:
        with transaction.atomic():  # 兩個請求同時送同一筆時，由資料庫的 unique 擋下
            record = UIEvent.objects.create(
                event_id=event_id,
                session_id=_text(payload["session_id"], 64),
                seq=seq,
                event_type=_text(payload["event_type"], 40),
                page_id=_text(payload["page_id"], 100),
                target_id=_text(payload.get("target_id") or "", 200),
                occurred_at=occurred_at,
                ui_version=_text(payload.get("ui_version") or "", 20),
                test_phase=_text(payload.get("test_phase") or "", 40),
                data=data,
            )
    except IntegrityError:
        record = UIEvent.objects.get(event_id=event_id)
        return JsonResponse({"success": True, "message": "事件已存在", "id": record.id})

    return JsonResponse({"success": True, "message": "事件已儲存", "id": record.id})


@require_POST
@csrf_protect
def receive_feedback(request):
    payload, error = _parse_json_object(request, MAX_FEEDBACK_BYTES)
    if error:
        return error

    page_id = payload.get("page_id")
    rating = payload.get("rating")
    comment = payload.get("comment")

    if not isinstance(page_id, str) or page_id not in FEEDBACK_PAGES:  # 先確認是字串：陣列放進 set 比對會丟 TypeError
        return _error("頁面識別碼錯誤")
    if rating not in ("like", "dislike"):
        return _error("請選擇有幫助或沒幫助")
    if not isinstance(comment, str):
        return _error("請填寫意見")
    comment = comment.replace("\x00", "").strip()
    if not comment:
        return _error("請填寫意見")
    if len(comment) > 2000:
        return _error("意見不可超過 2000 字")

    record = Feedback.objects.create(page_id=page_id, rating=rating, comment=comment)
    return JsonResponse({"success": True, "message": "感謝你的回饋，意見已儲存！", "id": record.id})
