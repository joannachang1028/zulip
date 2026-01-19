from unittest.mock import MagicMock, patch

from zerver.lib.test_classes import ZulipTestCase


class TopicTitleImproverTest(ZulipTestCase):
    def test_topic_title_suggestion_no_drift(self) -> None:
        """Test when topic title is appropriate."""
        self.login("hamlet")
        user = self.example_user("hamlet")
        stream = self.subscribe(user, "test stream")

        # Send a message to create a topic
        self.send_stream_message(user, "test stream", "Hello world", topic_name="Greetings")

        mock_response = MagicMock()
        mock_response.__getitem__ = lambda self, key: {
            "choices": [
                {
                    "message": {
                        "content": '{"has_drifted": false, "suggested_title": null, "reason": "The topic title matches the content."}'
                    }
                }
            ]
        }[key]

        with patch("zerver.actions.topic_title_improver.litellm.completion", return_value=mock_response):
            result = self.client_get(
                "/json/topic/suggest_title",
                {"stream_id": stream.id, "topic_name": "Greetings"},
            )

        self.assert_json_success(result)
        data = self.get_json(result)
        self.assertFalse(data["has_drifted"])
        self.assertIsNone(data["suggested_title"])

    def test_topic_title_suggestion_with_drift(self) -> None:
        """Test when topic has drifted and needs new title."""
        self.login("hamlet")
        user = self.example_user("hamlet")
        stream = self.subscribe(user, "test stream")

        # Send messages that drift from original topic
        self.send_stream_message(user, "test stream", "Let's discuss the budget", topic_name="Meeting Notes")
        self.send_stream_message(user, "test stream", "The Q4 projections look good", topic_name="Meeting Notes")

        mock_response = MagicMock()
        mock_response.__getitem__ = lambda self, key: {
            "choices": [
                {
                    "message": {
                        "content": '{"has_drifted": true, "suggested_title": "Q4 Budget Discussion", "reason": "The conversation is about budget and Q4 projections, not general meeting notes."}'
                    }
                }
            ]
        }[key]

        with patch("zerver.actions.topic_title_improver.litellm.completion", return_value=mock_response):
            result = self.client_get(
                "/json/topic/suggest_title",
                {"stream_id": stream.id, "topic_name": "Meeting Notes"},
            )

        self.assert_json_success(result)
        data = self.get_json(result)
        self.assertTrue(data["has_drifted"])
        self.assertEqual(data["suggested_title"], "Q4 Budget Discussion")

    def test_topic_title_suggestion_empty_topic(self) -> None:
        """Test with a topic that has no messages."""
        self.login("hamlet")
        user = self.example_user("hamlet")
        stream = self.subscribe(user, "test stream")

        result = self.client_get(
            "/json/topic/suggest_title",
            {"stream_id": stream.id, "topic_name": "NonexistentTopic"},
        )

        self.assert_json_success(result)
        data = self.get_json(result)
        self.assertFalse(data["has_drifted"])
        self.assertIn("No messages", data["reason"])
