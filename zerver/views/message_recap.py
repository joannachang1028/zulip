from django.http import HttpRequest, HttpResponse
from django.utils.translation import gettext as _

from zerver.actions.message_recap import do_generate_recap
from zerver.lib.exceptions import JsonableError
from zerver.lib.response import json_success
from zerver.lib.typed_endpoint import typed_endpoint_without_parameters
from zerver.models import UserProfile


@typed_endpoint_without_parameters
def get_messages_recap(request: HttpRequest, user_profile: UserProfile) -> HttpResponse:
    summary = do_generate_recap(user_profile)
    if summary is None:
        raise JsonableError(_("No unread messages to summarize."))

    return json_success(request, {"summary": summary})