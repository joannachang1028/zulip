import os
from unittest import mock

from typing_extensions import override

from zerver.lib.test_classes import ZulipTestCase


class MessageRecapTestCase(ZulipTestCase):
    @override
    def setUp(self) -> None:
        super().setUp()
        self.user = self.example_user("hamlet")
        self.other = self.example_user("iago")

        self.login_user(self.user)
        self.subscribe(self.user, "Denmark")

        # Two unread messages for hamlet.
        self.send_stream_message(self.other, "Denmark", content="Plan A ships tomorrow")
        self.send_stream_message(self.other, "Denmark", content="We need a quick recap")

        # Ensure litellm doesn't fetch cost map remotely during tests.
        os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
        os.environ["GROQ_API_KEY"] = "test-key"
        os.environ["LITELLM_MODEL"] = "groq/llama-3.3-70b-versatile"

        self.fake_response = {
            "choices": [
                {
                    "message": {
                        "content": "- Recap bullet with link to message"
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

    def test_recap_endpoint_returns_summary(self) -> None:
        with mock.patch("litellm.completion", return_value=self.fake_response):
            result = self.client_get("/json/messages/recap")
        self.assert_json_success(result)
        self.assertIn("summary", result.json())
        self.assertEqual(result.json()["summary"], "- Recap bullet with link to message")

    def test_recap_endpoint_no_unread(self) -> None:
        # Mark current messages as read, then expect error.
        self.client_post("/json/mark_all_as_read")
        with mock.patch("litellm.completion", return_value=self.fake_response):
            result = self.client_get("/json/messages/recap")
        self.assert_json_error_contains(result, "No unread messages")