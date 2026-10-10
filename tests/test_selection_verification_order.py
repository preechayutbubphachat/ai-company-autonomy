"""Selection must not consume verification grants for unselected lower-priority tasks."""
import unittest
from company_v1.company_core import choose
from company_v1.models import Task

def task(project, priority):
    return Task(project_id=project,task_id="T",action="BUILD",priority=priority,
                authority_revision=1,issuer_id="OWNER",expires_at=100)

class SelectionVerificationOrderTests(unittest.TestCase):
    def test_only_selected_candidate_is_verified(self):
        calls=[]
        class CountingVerifier:
            def verify(self,t,now):
                calls.append(t.project_id)
                return True
        selected=choose([task("low",1),task("high",10)],10,CountingVerifier())
        self.assertEqual(selected.task.project_id,"high")
        self.assertEqual(calls,["high"])
        self.assertFalse(selected.dispatch_allowed)

    def test_fallback_to_lower_priority_when_top_denied(self):
        calls=[]
        class SelectiveVerifier:
            def verify(self,t,now):
                calls.append(t.project_id)
                return t.project_id=="low"
        selected=choose([task("low",1),task("high",10)],10,SelectiveVerifier())
        self.assertEqual(selected.task.project_id,"low")
        self.assertEqual(calls,["high","low"])
        self.assertFalse(selected.dispatch_allowed)

    def test_duplicate_ids_deny_before_verification(self):
        calls=[]
        class CountingVerifier:
            def verify(self,t,now):
                calls.append(t.project_id)
                return True
        t=task("p",1)
        selected=choose([t,t],10,CountingVerifier())
        self.assertEqual(selected.reason,"DUPLICATE_TASK_ID")
        self.assertEqual(calls,[])
