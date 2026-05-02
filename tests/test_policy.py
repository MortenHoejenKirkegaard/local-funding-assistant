from pathlib import Path

import pytest

from funding_assistant.policy import resolve_inside_root, validate_action


def test_local_read_is_allowed():
    decision = validate_action("local_read")

    assert decision.decision == "allowed"


def test_api_analysis_requires_approval():
    decision = validate_action("api_analysis")

    assert decision.decision == "requires_approval"


@pytest.mark.parametrize(
    "action_type",
    [
        "purchase",
        "agreement",
        "external_submission",
        "account_creation",
        "email_send",
        "data_share",
        "file_upload",
        "third_party_message",
    ],
)
def test_external_and_spending_actions_are_blocked(action_type):
    decision = validate_action(action_type)

    assert decision.decision == "blocked"


def test_unknown_actions_are_blocked_by_default():
    decision = validate_action("invented_future_action")

    assert decision.decision == "blocked"


def test_slack_output_to_owner_without_confidential_content_is_allowed():
    decision = validate_action(
        "slack_output",
        {
            "recipient_is_owner": True,
            "contains_confidential_content": False,
            "contains_full_document": False,
            "contains_full_draft": False,
        },
    )

    assert decision.decision == "allowed"


def test_slack_output_to_non_owner_is_blocked():
    decision = validate_action("slack_output", {"recipient_is_owner": False})

    assert decision.decision == "blocked"


@pytest.mark.parametrize(
    "payload",
    [
        {"recipient_is_owner": True, "contains_confidential_content": True},
        {"recipient_is_owner": True, "contains_full_document": True},
        {"recipient_is_owner": True, "contains_full_draft": True},
    ],
)
def test_slack_output_with_sensitive_content_is_blocked(payload):
    decision = validate_action("slack_output", payload)

    assert decision.decision == "blocked"


def test_path_inside_allowed_root_resolves():
    root = Path("/tmp/codex-access-test-root")
    candidate = root / "funding-assistant" / "cases" / "company-01"

    resolved = resolve_inside_root(candidate, root)

    assert resolved == candidate.resolve()


def test_path_outside_allowed_root_is_rejected():
    root = Path("/tmp/codex-access-test-root")
    outside = Path("/tmp/other-place/file.docx")

    with pytest.raises(ValueError):
        resolve_inside_root(outside, root)

