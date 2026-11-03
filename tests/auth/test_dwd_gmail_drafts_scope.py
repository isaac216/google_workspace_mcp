"""Service-account mode keeps requesting gmail.compose for drafting, as before gmail.drafts.create existed."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from auth.scopes import (
    GMAIL_COMPOSE_SCOPE,
    GMAIL_DRAFTS_CREATE_SCOPE,
    GMAIL_READONLY_SCOPE,
)
from auth.service_decorator import _widen_gmail_drafts_scope_for_dwd


def test_drafts_create_is_widened_to_compose():
    assert _widen_gmail_drafts_scope_for_dwd(
        [GMAIL_DRAFTS_CREATE_SCOPE], "draft_gmail_message"
    ) == [GMAIL_COMPOSE_SCOPE]


def test_other_scopes_are_left_alone():
    scopes = [GMAIL_READONLY_SCOPE]
    assert _widen_gmail_drafts_scope_for_dwd(scopes, "search_gmail_messages") == scopes


def test_widening_does_not_duplicate_compose():
    scopes = [GMAIL_READONLY_SCOPE, GMAIL_COMPOSE_SCOPE, GMAIL_DRAFTS_CREATE_SCOPE]
    assert _widen_gmail_drafts_scope_for_dwd(scopes, "draft_gmail_message") == [
        GMAIL_READONLY_SCOPE,
        GMAIL_COMPOSE_SCOPE,
    ]
