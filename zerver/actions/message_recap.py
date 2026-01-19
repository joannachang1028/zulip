import orjson
from typing import Any

from django.utils.translation import gettext as _

from zerver.lib.llm_config import load_llm_config
from zerver.lib.message import get_raw_unread_data, messages_for_ids
from zerver.lib.url_encoding import message_link_url
from zerver.models import UserProfile
from zerver.models.realms import MessageEditHistoryVisibilityPolicyEnum

# Cap the number of unread messages we send to the LLM to keep cost/latency reasonable.
MAX_RECAP_MESSAGES = 80


def _collect_unread_message_ids(raw_data: dict[str, Any]) -> list[int]:
    # Use the same sources as the unread count shown to users: unmuted stream msgs, DMs, huddles.
    message_ids = set(raw_data["unmuted_stream_msgs"])
    message_ids.update(raw_data["pm_dict"].keys())
    message_ids.update(raw_data["huddle_dict"].keys())
    # Sort ascending and keep the most recent slice.
    sorted_ids = sorted(message_ids)
    if len(sorted_ids) > MAX_RECAP_MESSAGES:
        sorted_ids = sorted_ids[-MAX_RECAP_MESSAGES:]
    return sorted_ids


def _format_messages_for_model(message_list: list[dict[str, Any]]) -> str:
    payload = []
    for message in message_list:
        payload.append(
            {
                "id": message["id"],
                "sender": message["sender_full_name"],
                "topic": message.get("topic", ""),
                "content": message["content"],
                "url": message_link_url(message["realm"], message),
            }
        )
    return orjson.dumps(payload).decode()


def _build_prompt(message_list: list[dict[str, Any]]) -> list[dict[str, str]]:
    intro = (
        "You are summarizing a user's unread Zulip messages. "
        "Input is a JSON array of messages with fields id, sender, topic, content, url. "
        "Return a concise recap in Markdown using at most 8 bullet points. "
        "Each bullet should include an inline link to the most relevant message using the provided url. "
        "Focus on key decisions, actions, and questions. Keep it short and skimmable."
    )

    formatted = _format_messages_for_model(message_list)

    return [
        {"role": "system", "content": intro},
        {
            "role": "user",
            "content": f"Unread messages JSON:\n{formatted}\nProduce the recap now.",
        },
    ]


def do_generate_recap(user_profile: UserProfile) -> str | None:
    raw_unread = get_raw_unread_data(user_profile)
    message_ids = _collect_unread_message_ids(raw_unread)
    if not message_ids:
        return None

    user_message_flags = {message_id: [] for message_id in message_ids}

    message_list = messages_for_ids(
        message_ids=message_ids,
        user_message_flags=user_message_flags,
        search_fields={},
        apply_markdown=False,
        client_gravatar=True,
        allow_empty_topic_name=True,
        message_edit_history_visibility_policy=MessageEditHistoryVisibilityPolicyEnum.none.value,
        user_profile=user_profile,
        realm=user_profile.realm,
    )

    # Attach realm to each message dict for URL construction.
    for message in message_list:
        message["realm"] = user_profile.realm

    messages = _build_prompt(message_list)

    config = load_llm_config()

    # Import inside function to avoid import cost if feature unused.
    import litellm

    response = litellm.completion(
        model=config["model"],
        messages=messages,
    )

    summary = response["choices"][0]["message"]["content"].strip()
    return summary