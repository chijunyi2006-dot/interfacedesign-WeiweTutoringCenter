"""python manage.py test tracking：驗證兩個 API 的成功與失敗情況。"""
import json

from django.test import Client, TestCase

from .models import Feedback, UIEvent


def valid_event(**changes):
    event = {
        "event_id": "evt-1", "session_id": "sess-1", "seq": 1, "event_type": "nav_click",
        "page_id": "home", "target_id": "nav_teachers", "occurred_at": "2026-11-16T05:20:31.000Z",
        "ui_version": "v1", "test_phase": "week11", "data": {"result_count": 4},
    }
    event.update(changes)
    return event


class EventApiTests(TestCase):
    def post(self, payload, client=None):
        client = client or Client()
        body = payload if isinstance(payload, str) else json.dumps(payload)
        return client.post("/api/events/", body, content_type="application/json")

    def test_saves_valid_event(self):
        response = self.post(valid_event())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        record = UIEvent.objects.get(id=response.json()["id"])
        self.assertEqual((record.event_type, record.page_id, record.data["result_count"]), ("nav_click", "home", 4))

    def test_duplicate_event_id_is_saved_once(self):
        self.post(valid_event())
        response = self.post(valid_event())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(UIEvent.objects.count(), 1)

    def test_missing_required_field_is_400(self):
        event = valid_event()
        del event["page_id"]
        response = self.post(event)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(UIEvent.objects.count(), 0)

    def test_bad_json_and_non_object_are_400(self):
        self.assertEqual(self.post("{壞掉的 json").status_code, 400)
        self.assertEqual(self.post("[1, 2]").status_code, 400)

    def test_bad_time_seq_and_data_are_400(self):
        self.assertEqual(self.post(valid_event(occurred_at="昨天")).status_code, 400)
        self.assertEqual(self.post(valid_event(occurred_at="2026-11-16T05:20:31")).status_code, 400)  # 沒有時區
        self.assertEqual(self.post(valid_event(seq="abc")).status_code, 400)
        self.assertEqual(self.post(valid_event(data=[1])).status_code, 400)

    def test_optional_fields_default_to_empty(self):
        event = valid_event()
        for name in ("target_id", "ui_version", "test_phase", "data"):
            del event[name]
        response = self.post(event)
        self.assertEqual(response.status_code, 200)
        record = UIEvent.objects.get()
        self.assertEqual((record.target_id, record.ui_version, record.data), ("", "", {}))

    def test_get_is_405_and_missing_csrf_is_403(self):
        self.assertEqual(Client().get("/api/events/").status_code, 405)
        strict = Client(enforce_csrf_checks=True)
        self.assertEqual(self.post(valid_event(), strict).status_code, 403)


    def test_data_keeps_only_whitelisted_fields(self):
        data = {"result_count": 4, "phone": "0912345678", "selected_value": "研" * 100, "nested": {"a": 1}}
        response = self.post(valid_event(data=data))
        self.assertEqual(response.status_code, 200)
        record = UIEvent.objects.get()
        self.assertEqual(set(record.data), {"result_count", "selected_value"})
        self.assertEqual(len(record.data["selected_value"]), 60)

    def test_seq_must_be_real_integer_in_range(self):
        for bad in (True, 2.7, -1, 2_147_483_648, "1.5"):
            self.assertEqual(self.post(valid_event(event_id=f"e{bad}", seq=bad)).status_code, 400, bad)
        self.assertEqual(self.post(valid_event(seq="3")).status_code, 200)
        self.assertEqual(UIEvent.objects.get().seq, 3)

    def test_impossible_date_and_blank_required_are_400(self):
        self.assertEqual(self.post(valid_event(occurred_at="2026-13-40T05:20:31Z")).status_code, 400)
        self.assertEqual(self.post(valid_event(session_id="   ")).status_code, 400)

    def test_nul_characters_are_removed(self):
        response = self.post(valid_event(target_id="nav\x00_x", data={"reason": "a\x00b"}))
        self.assertEqual(response.status_code, 200)
        record = UIEvent.objects.get()
        self.assertEqual((record.target_id, record.data["reason"]), ("nav_x", "ab"))

    def test_oversized_body_is_413(self):
        response = self.post(valid_event(target_id="x" * 11_000))
        self.assertEqual(response.status_code, 413)


class FeedbackApiTests(TestCase):
    def post(self, payload, client=None):
        client = client or Client()
        return client.post("/api/feedback/", json.dumps(payload), content_type="application/json")

    def test_saves_feedback(self):
        response = self.post({"page_id": "courses", "rating": "dislike", "comment": " 找不到費用 "})
        self.assertEqual(response.status_code, 200)
        record = Feedback.objects.get(id=response.json()["id"])
        self.assertEqual((record.page_id, record.rating, record.comment), ("courses", "dislike", "找不到費用"))

    def test_rejects_bad_input(self):
        base = {"page_id": "home", "rating": "like", "comment": "好用"}
        for change in ({"page_id": "hacker"}, {"rating": "meh"}, {"comment": "   "}, {"comment": "字" * 2001}, {"comment": 5},
                       {"page_id": ["home"]}, {"page_id": {"a": 1}}, {"rating": ["like"]}):
            self.assertEqual(self.post({**base, **change}).status_code, 400, change)
        self.assertEqual(Feedback.objects.count(), 0)

    def test_missing_csrf_is_403(self):
        strict = Client(enforce_csrf_checks=True)
        self.assertEqual(self.post({"page_id": "home", "rating": "like", "comment": "好用"}, strict).status_code, 403)
