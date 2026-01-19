from django.http import HttpRequest, HttpResponse

from zerver.actions.topic_title_improver import do_analyze_topic_title
from zerver.lib.response import json_success
from zerver.lib.typed_endpoint import typed_endpoint
from zerver.models import UserProfile


@typed_endpoint
def get_topic_title_suggestion(
    request: HttpRequest,
    user_profile: UserProfile,
    *,
    stream_id: str,
    topic_name: str,
) -> HttpResponse:
    result = do_analyze_topic_title(user_profile, int(stream_id), topic_name)
    return json_success(request, result)
