"""
自动化测试 - 多审批人审批机制
题目: Implement Multiple Reviewer Approval for Bounty Submissions
"""

import unittest

from solution import (
    ApprovalStatus,
    BountySubmissionManager,
    SubmissionStatus,
)


class TestMultiReviewerApproval(unittest.TestCase):
    def setUp(self):
        self.mgr = BountySubmissionManager()

    def test_create_submission(self):
        sub = self.mgr.create_submission("T", "D", "author-1", required_approvals=2)
        self.assertEqual(sub.status, SubmissionStatus.DRAFT)
        self.assertEqual(sub.required_approvals, 2)

    def test_submit_for_review(self):
        sub = self.mgr.create_submission("T", "D", "author-1")
        self.assertTrue(self.mgr.submit_for_review(sub.submission_id))
        self.assertEqual(self.mgr.get_submission(sub.submission_id).status, SubmissionStatus.IN_REVIEW)

    def test_submit_twice_rejected(self):
        sub = self.mgr.create_submission("T", "D", "author-1")
        self.mgr.submit_for_review(sub.submission_id)
        self.assertFalse(self.mgr.submit_for_review(sub.submission_id))

    def test_add_reviewer(self):
        sub = self.mgr.create_submission("T", "D", "author-1")
        self.assertTrue(self.mgr.add_reviewer(sub.submission_id, "r1"))
        self.assertFalse(self.mgr.add_reviewer(sub.submission_id, "r1"))  # 重复添加

    def test_approval_reaches_threshold(self):
        sub = self.mgr.create_submission("T", "D", "author-1", required_approvals=2)
        self.mgr.add_reviewer(sub.submission_id, "r1")
        self.mgr.add_reviewer(sub.submission_id, "r2")
        self.mgr.submit_for_review(sub.submission_id)
        self.mgr.review(sub.submission_id, "r1", ApprovalStatus.APPROVED, "ok")
        # 只有一个审批，未达阈值
        self.assertEqual(self.mgr.get_submission(sub.submission_id).status, SubmissionStatus.IN_REVIEW)
        self.mgr.review(sub.submission_id, "r2", ApprovalStatus.APPROVED, "ok")
        self.assertTrue(self.mgr.is_fully_approved(sub.submission_id))

    def test_one_rejection_rejects_submission(self):
        sub = self.mgr.create_submission("T", "D", "author-1", required_approvals=2)
        self.mgr.add_reviewer(sub.submission_id, "r1")
        self.mgr.add_reviewer(sub.submission_id, "r2")
        self.mgr.submit_for_review(sub.submission_id)
        self.mgr.review(sub.submission_id, "r1", ApprovalStatus.APPROVED, "ok")
        self.mgr.review(sub.submission_id, "r2", ApprovalStatus.REJECTED, "issues")
        self.assertEqual(self.mgr.get_submission(sub.submission_id).status, SubmissionStatus.REJECTED)

    def test_review_nonexistent(self):
        self.assertFalse(self.mgr.review("nope", "r1", ApprovalStatus.APPROVED))


if __name__ == "__main__":
    unittest.main()
