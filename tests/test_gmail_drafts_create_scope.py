"""
Tests for the gmail.drafts.create scope and the gmail "create_drafts" level.

gmail.drafts.create lets an app create drafts without being able to send mail
(gmail.compose and gmail.modify can both send). The "create_drafts" level
requests only gmail.readonly plus gmail.drafts.create, so a deployment can let
an agent read mail and leave drafts for a human to review and send. Adding the
level must not change what any existing level requests from Google.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from auth.permissions import (  # noqa: E402
    get_allowed_scopes_set,
    get_scopes_for_permission,
    parse_permissions_arg,
    set_permissions,
)
from auth.scopes import (  # noqa: E402
    GMAIL_COMPOSE_SCOPE,
    GMAIL_DRAFTS_CREATE_SCOPE,
    GMAIL_LABELS_SCOPE,
    GMAIL_MODIFY_SCOPE,
    GMAIL_READONLY_SCOPE,
    GMAIL_SEND_SCOPE,
    GMAIL_SETTINGS_BASIC_SCOPE,
    has_required_scopes,
)

FULL_MAIL_SCOPE = "https://mail.google.com/"
SEND_CAPABLE = {
    GMAIL_COMPOSE_SCOPE,
    GMAIL_SEND_SCOPE,
    GMAIL_MODIFY_SCOPE,
    FULL_MAIL_SCOPE,
}

# What each pre-existing level requested from Google before create_drafts existed (v2.3.0).
LEVELS_BEFORE = {
    "readonly": {GMAIL_READONLY_SCOPE},
    "organize": {GMAIL_READONLY_SCOPE, GMAIL_LABELS_SCOPE, GMAIL_MODIFY_SCOPE},
    "drafts": {
        GMAIL_READONLY_SCOPE,
        GMAIL_LABELS_SCOPE,
        GMAIL_MODIFY_SCOPE,
        GMAIL_COMPOSE_SCOPE,
    },
    "send": {
        GMAIL_READONLY_SCOPE,
        GMAIL_LABELS_SCOPE,
        GMAIL_MODIFY_SCOPE,
        GMAIL_COMPOSE_SCOPE,
        GMAIL_SEND_SCOPE,
    },
    "full": {
        GMAIL_READONLY_SCOPE,
        GMAIL_LABELS_SCOPE,
        GMAIL_MODIFY_SCOPE,
        GMAIL_COMPOSE_SCOPE,
        GMAIL_SEND_SCOPE,
        GMAIL_SETTINGS_BASIC_SCOPE,
    },
}


@pytest.fixture
def permissions():
    def _set(levels):
        set_permissions(levels)
        return get_allowed_scopes_set()

    yield _set
    set_permissions(None)


def _required(tool):
    fn = getattr(tool, "fn", tool)
    return set(getattr(fn, "_required_google_scopes", []))


def test_scope_url():
    assert (
        GMAIL_DRAFTS_CREATE_SCOPE
        == "https://www.googleapis.com/auth/gmail.drafts.create"
    )


def test_create_drafts_level_requests_readonly_and_drafts_create_only():
    assert set(get_scopes_for_permission("gmail", "create_drafts")) == {
        GMAIL_READONLY_SCOPE,
        GMAIL_DRAFTS_CREATE_SCOPE,
    }


@pytest.mark.parametrize(
    "level", ["create_drafts", "readonly+create_drafts", "create_drafts+readonly"]
)
def test_create_drafts_never_requests_a_send_capable_scope(level):
    assert not set(get_scopes_for_permission("gmail", level)) & SEND_CAPABLE


def test_parse_accepts_create_drafts():
    assert parse_permissions_arg(["gmail:create_drafts"]) == {"gmail": "create_drafts"}


@pytest.mark.parametrize("level", sorted(LEVELS_BEFORE))
def test_existing_levels_request_the_same_scopes_as_before(level):
    assert set(get_scopes_for_permission("gmail", level)) == LEVELS_BEFORE[level]


def test_existing_union_requests_the_same_scopes_as_before():
    assert set(get_scopes_for_permission("gmail", "readonly+drafts")) == {
        GMAIL_READONLY_SCOPE,
        GMAIL_COMPOSE_SCOPE,
    }


def test_compose_and_modify_cover_drafts_create():
    assert has_required_scopes([GMAIL_COMPOSE_SCOPE], [GMAIL_DRAFTS_CREATE_SCOPE])
    assert has_required_scopes([GMAIL_MODIFY_SCOPE], [GMAIL_DRAFTS_CREATE_SCOPE])


def test_drafts_create_covers_neither_compose_nor_send():
    assert not has_required_scopes([GMAIL_DRAFTS_CREATE_SCOPE], [GMAIL_COMPOSE_SCOPE])
    assert not has_required_scopes([GMAIL_DRAFTS_CREATE_SCOPE], [GMAIL_SEND_SCOPE])
    assert not has_required_scopes([GMAIL_READONLY_SCOPE], [GMAIL_DRAFTS_CREATE_SCOPE])


def test_draft_tool_declares_drafts_create():
    from gmail import gmail_tools

    assert _required(gmail_tools.draft_gmail_message) == {GMAIL_DRAFTS_CREATE_SCOPE}


def test_create_drafts_level_keeps_draft_tool_and_drops_send_tool(permissions):
    from gmail import gmail_tools

    allowed = permissions({"gmail": "create_drafts"})
    assert _required(gmail_tools.draft_gmail_message) <= allowed
    assert not _required(gmail_tools.send_gmail_message) <= allowed


@pytest.mark.parametrize("level", ["drafts", "readonly+drafts", "send", "full"])
def test_compose_levels_still_get_the_draft_tool(permissions, level):
    from gmail import gmail_tools

    assert _required(gmail_tools.draft_gmail_message) <= permissions({"gmail": level})


def test_organize_level_still_excludes_the_draft_tool(permissions):
    from gmail import gmail_tools

    assert not _required(gmail_tools.draft_gmail_message) <= permissions(
        {"gmail": "organize"}
    )
