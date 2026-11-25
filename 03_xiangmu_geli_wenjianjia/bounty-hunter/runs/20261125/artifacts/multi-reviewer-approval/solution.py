"""
多审批人审批机制 - Bounty 提交流程

题目: Implement Multiple Reviewer Approval for Bounty Submissions
平台: github_bounties_public
类型: 功能实现 / Python
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_CHANGES = "requires_changes"


class SubmissionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    MERGED = "merged"


@dataclass
class ReviewerApproval:
    reviewer_id: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    comment: str = ""
    reviewed_at: Optional[str] = None


@dataclass
class BountySubmission:
    submission_id: str
    title: str
    description: str
    author_id: str
    status: SubmissionStatus = SubmissionStatus.DRAFT
    approvals: List[ReviewerApproval] = field(default_factory=list)
    required_approvals: int = 2
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat() + "Z")
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat() + "Z")


class BountySubmissionManager:
    """管理 bounty 提交的多审批人审批流程"""

    def __init__(self) -> None:
        self._submissions: Dict[str, BountySubmission] = {}

    def create_submission(
        self,
        title: str,
        description: str,
        author_id: str,
        required_approvals: int = 2,
    ) -> BountySubmission:
        submission = BountySubmission(
            submission_id=str(uuid.uuid4()),
            title=title,
            description=description,
            author_id=author_id,
            required_approvals=required_approvals,
        )
        self._submissions[submission.submission_id] = submission
        return submission

    def submit_for_review(self, submission_id: str) -> bool:
        submission = self._submissions.get(submission_id)
        if not submission:
            return False
        if submission.status != SubmissionStatus.DRAFT:
            return False
        submission.status = SubmissionStatus.IN_REVIEW
        submission.updated_at = datetime.now(timezone.utc).isoformat() + "Z"
        return True

    def add_reviewer(self, submission_id: str, reviewer_id: str) -> bool:
        submission = self._submissions.get(submission_id)
        if not submission:
            return False
        if any(a.reviewer_id == reviewer_id for a in submission.approvals):
            return False
        submission.approvals.append(ReviewerApproval(reviewer_id=reviewer_id))
        submission.updated_at = datetime.now(timezone.utc).isoformat() + "Z"
        return True

    def review(self, submission_id: str, reviewer_id: str, status: ApprovalStatus, comment: str = "") -> bool:
        submission = self._submissions.get(submission_id)
        if not submission or submission.status != SubmissionStatus.IN_REVIEW:
            return False

        for approval in submission.approvals:
            if approval.reviewer_id == reviewer_id:
                approval.status = status
                approval.comment = comment
                approval.reviewed_at = datetime.now(timezone.utc).isoformat() + "Z"
                break
        else:
            return False

        # 统计已批准和已拒绝的数量
        approved_count = sum(1 for a in submission.approvals if a.status == ApprovalStatus.APPROVED)
        rejected_count = sum(1 for a in submission.approvals if a.status == ApprovalStatus.REJECTED)

        if rejected_count > 0:
            submission.status = SubmissionStatus.REJECTED
        elif approved_count >= submission.required_approvals:
            submission.status = SubmissionStatus.APPROVED

        submission.updated_at = datetime.now(timezone.utc).isoformat() + "Z"
        return True

    def get_submission(self, submission_id: str) -> Optional[BountySubmission]:
        return self._submissions.get(submission_id)

    def is_fully_approved(self, submission_id: str) -> bool:
        submission = self._submissions.get(submission_id)
        if not submission:
            return False
        return submission.status == SubmissionStatus.APPROVED


if __name__ == "__main__":
    # 快速自测
    mgr = BountySubmissionManager()
    sub = mgr.create_submission(
        title="Fix parse_duration days unit",
        description="Add support for 'd' unit in parse_duration",
        author_id="user-123",
        required_approvals=2,
    )
    mgr.add_reviewer(sub.submission_id, "reviewer-a")
    mgr.add_reviewer(sub.submission_id, "reviewer-b")
    mgr.submit_for_review(sub.submission_id)
    mgr.review(sub.submission_id, "reviewer-a", ApprovalStatus.APPROVED, "LGTM")
    mgr.review(sub.submission_id, "reviewer-b", ApprovalStatus.APPROVED, "Looks good")
    print(f"Submission {sub.submission_id} status: {sub.status.value}")
    assert sub.status == SubmissionStatus.APPROVED
    print("自测通过")
