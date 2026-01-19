import orjson
from typing import Any

from zerver.lib.llm_config import load_llm_config
from zerver.lib.message import messages_for_ids
from zerver.models import Message, UserProfile
from zerver.models.realms import MessageEditHistoryVisibilityPolicyEnum

# Max messages to analyze for topic drift
MAX_TOPIC_MESSAGES = 30


def _get_recent_topic_messages(
    user_profile: UserProfile, stream_id: int, topic_name: str
) -> list[dict[str, Any]]:
    """Fetch recent messages from a specific topic."""
    message_ids = list(
        Message.objects.filter(
            realm_id=user_profile.realm_id,
            recipient__type_id=stream_id,
            subject__iexact=topic_name,
        )
        .order_by("-id")[:MAX_TOPIC_MESSAGES]
        .values_list("id", flat=True)
    )

    if not message_ids:
        return []

    user_message_flags = {msg_id: [] for msg_id in message_ids}

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

    return message_list


def _format_messages_for_analysis(message_list: list[dict[str, Any]]) -> str:
    """Format messages for LLM analysis."""
    payload = []
    for message in message_list:
        payload.append(
            {
                "sender": message["sender_full_name"],
                "content": message["content"],
            }
        )
    return orjson.dumps(payload).decode()


def _build_analysis_prompt(
    topic_name: str, messages_json: str
) -> list[dict[str, str]]:
    """Build prompt to analyze topic drift and suggest better title."""
    system_prompt = (
        "You are analyzing a Zulip topic to determine if the conversation has drifted "
        "from the original topic title. You will be given the current topic title and "
        "recent messages in the topic.\n\n"
        "Your task:\n"
        "1. Analyze if the conversation content matches the topic title\n"
        "2. If the content has drifted significantly, suggest a better title\n"
        "3. Respond in JSON format with these fields:\n"
        '   - "has_drifted": boolean (true if content no longer matches title)\n'
        '   - "suggested_title": string (new title, or null if no drift)\n'
        '   - "reason": string (brief explanation of your analysis)\n\n'
        "Keep suggested titles concise (under 60 characters) and descriptive."
    )

    user_prompt = (
        f"Current topic title: {topic_name}\n\n"
        f"Recent messages:\n{messages_json}\n\n"
        "Analyze and respond with JSON only."
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def do_analyze_topic_title(
    user_profile: UserProfile, stream_id: int, topic_name: str
) -> dict[str, Any]:
    """
    Analyze a topic and suggest a better title if the conversation has drifted.

    Returns a dict with:
    - has_drifted: bool
    - suggested_title: str | None
    - reason: str
    """
    message_list = _get_recent_topic_messages(user_profile, stream_id, topic_name)

    if not message_list:
        return {
            "has_drifted": False,
            "suggested_title": None,
            "reason": "No messages found in this topic.",
        }

    messages_json = _format_messages_for_analysis(message_list)
    prompt = _build_analysis_prompt(topic_name, messages_json)

    config = load_llm_config()

    import litellm

    response = litellm.completion(
        model=config["model"],
        messages=prompt,
        response_format={"type": "json_object"},
    )

    result_text = response["choices"][0]["message"]["content"].strip()

    try:
        result = orjson.loads(result_text)
        return {
            "has_drifted": result.get("has_drifted", False),
            "suggested_title": result.get("suggested_title"),
            "reason": result.get("reason", ""),
        }
    except orjson.JSONDecodeError:
        # If LLM didn't return valid JSON, return safe default
        return {
            "has_drifted": False,
            "suggested_title": None,
            "reason": "Unable to analyze topic.",
        }
