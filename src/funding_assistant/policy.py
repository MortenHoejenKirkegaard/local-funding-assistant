from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


ALLOWED_ACTIONS = {"local_read", "local_write", "slack_output"}
APPROVAL_ACTIONS = {"api_analysis"}
BLOCKED_ACTIONS = {
    "external_submission",
    "purchase",
    "agreement",
    "account_creation",
    "email_send",
    "data_share",
    "file_upload",
    "third_party_message",
}


@dataclass(frozen=True)
class PolicyDecision:
    decision: str
    reason: str

    @property
    def allowed(self) -> bool:
        return self.decision == "allowed"


def resolve_inside_root(candidate_path: str | Path, allowed_root: str | Path) -> Path:
    root = Path(allowed_root).expanduser().resolve()
    candidate = Path(candidate_path).expanduser().resolve()

    if candidate != root and root not in candidate.parents:
        raise ValueError(f"Path is outside allowed root: {candidate}")

    return candidate


def validate_action(action_type: str, payload: dict[str, Any] | None = None) -> PolicyDecision:
    payload = payload or {}

    if action_type in ALLOWED_ACTIONS:
        if action_type == "slack_output":
            return _validate_slack_output(payload)
        return PolicyDecision("allowed", "Local action is allowed.")

    if action_type in APPROVAL_ACTIONS:
        return PolicyDecision("requires_approval", "API analysis requires explicit cost approval.")

    if action_type in BLOCKED_ACTIONS:
        return PolicyDecision("blocked", f"Action type is blocked by policy: {action_type}")

    return PolicyDecision("blocked", f"Unknown action type is blocked by default: {action_type}")


def _validate_slack_output(payload: dict[str, Any]) -> PolicyDecision:
    recipient_is_owner = payload.get("recipient_is_owner", False)
    contains_confidential_content = payload.get("contains_confidential_content", False)
    contains_full_document = payload.get("contains_full_document", False)
    contains_full_draft = payload.get("contains_full_draft", False)

    if not recipient_is_owner:
        return PolicyDecision("blocked", "Slack output is only allowed to the owner.")

    if contains_confidential_content or contains_full_document or contains_full_draft:
        return PolicyDecision("blocked", "Slack output may only contain non-confidential summaries.")

    return PolicyDecision("allowed", "Slack owner summary is allowed.")

