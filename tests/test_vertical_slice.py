import tempfile
import unittest
from pathlib import Path

from company_v1.models import CANONICAL_PROFILES, DenyAllVerifier, Task, TestOnlyVerifier
from company_v1.company_core import choose
from company_v1.agent_adapters import DispatchDenied, dispatch_live, plan_adapter
from company_v1.security import GateSnapshot
from company_v1.project_isolation import ProjectScopeError, require_scope
from company_v1.verifier import pending
from company_v1.supervisor_mechanical import tick
from company_v1.durable_ledger import DurableLedger, LedgerConflict


def task(project='P-A', taskid='T-1', priority=4, **changes):
    data=dict(project_id=project,task_id=taskid,action='BUILD',priority=priority,
              authority_revision=2,issuer_id='OWNER',expires_at=100,
              owner_required=False,security_hold=False,revoked=False,source_version=1)
    data.update(changes)
    return Task(**data)


def allowed(*ts):
    return TestOnlyVerifier({(t.issuer_id,t.project_id,t.action,t.authority_revision) for t in ts})

class CoreTests(unittest.TestCase):
    def test_deny_by_default(self):
        self.assertIsNone(choose([task()],10).task)
    def test_empty_candidates(self):
        self.assertIsNone(choose([],10).task)
    def test_verifier_selects(self):
        a=task(); self.assertEqual(choose([a],10,allowed(a)).task,a)
    def test_expired_denied(self):
        a=task();self.assertIsNone(choose([a],100,allowed(a)).task)
    def test_revoked_denied(self):
        a=task(revoked=True);self.assertIsNone(choose([a],10,allowed(a)).task)
    def test_security_hold_denied(self):
        a=task(security_hold=True);self.assertIsNone(choose([a],10,allowed(a)).task)
    def test_owner_gate_denied(self):
        a=task(owner_required=True);self.assertIsNone(choose([a],10,allowed(a)).task)
    def test_priority(self):
        a=task('P-A','T-1',1); b=task('P-B','T-2',5)
        self.assertEqual(choose([a,b],10,allowed(a,b)).task,b)
    def test_deterministic_tie(self):
        a=task('P-A','T-1');b=task('P-B','T-2')
        self.assertEqual(choose([b,a],10,allowed(a,b)).task,a)
    def test_duplicate_fail_closed(self):
        a=task();self.assertEqual(choose([a,a],10,allowed(a)).reason,'DUPLICATE_TASK_ID')
    def test_missing_identity_fail_closed(self):
        a=task(project='');self.assertIsNone(choose([a],10,allowed(a)).task)
    def test_different_issuer_untrusted(self):
        a=task();other=task(issuer_id='UNTRUSTED')
        self.assertIsNone(choose([other],10,allowed(a)).task)
    def test_wrong_revision_untrusted(self):
        a=task();other=task(authority_revision=3)
        self.assertIsNone(choose([other],10,allowed(a)).task)
    def test_no_dispatch_even_with_test_verifier(self):
        a=task();self.assertFalse(choose([a],10,allowed(a)).dispatch_allowed)
    def test_test_verifier_never_bypasses_expiry(self):
        a=task();self.assertFalse(allowed(a).verify(a,100))

class BoundaryTests(unittest.TestCase):
    def test_five_profiles_exact(self):
        self.assertEqual(len(CANONICAL_PROFILES),5)
    def test_adapter_dry_run(self):
        for p in CANONICAL_PROFILES:
            self.assertFalse(plan_adapter(p,'P-A','BUILD')['dispatch_allowed'])
    def test_sixth_agent_denied(self):
        with self.assertRaises(DispatchDenied):plan_adapter('agent-six','P-A','BUILD')
    def test_live_dispatch_denied(self):
        with self.assertRaises(DispatchDenied):dispatch_live()
    def test_project_scope(self):
        require_scope('P-A','P-A')
        with self.assertRaises(ProjectScopeError):require_scope('P-A','P-B')
    def test_gate_default_denied(self):
        self.assertFalse(GateSnapshot().permit_real_execution())
    def test_all_gate_flags_still_not_certification(self):
        self.assertFalse(GateSnapshot(True,True,True,True).permit_real_execution())
    def test_independent_review_not_faked(self):
        a=pending('example_sha');self.assertEqual(a.status,'NOT_RUN');self.assertFalse(a.independent)
    def test_supervisor_request_only(self):
        a=task();p=tick([a],10,allowed(a))
        self.assertTrue(p.request_rin);self.assertFalse(p.dispatch_allowed)
    def test_supervisor_default_denied(self):
        self.assertFalse(tick([task()],10).request_rin)
    def test_supervisor_held_project_skipped(self):
        a=task('P-A','TA',99,security_hold=True);b=task('P-B','TB',1)
        self.assertEqual(tick([a,b],10,allowed(a,b)).candidate,'P-B/TB')

class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='clean-source-v1-')
        self.db=Path(self.temp.name)/'state.sqlite3'
        self.store=DurableLedger(self.db)
        self.store.enqueue_test_only('P-A','T-1',2)
    def tearDown(self):
        self.store.close();self.temp.cleanup()
    def test_enqueue(self):
        self.assertEqual(self.store.inspect_test_only('P-A','T-1'),('READY',0))
    def test_initial_claim(self):
        self.assertEqual(self.store.claim_test_only('P-A','T-1','worker',10,20,2),1)
    def test_double_claim_denied(self):
        self.store.claim_test_only('P-A','T-1','worker',10,20,2)
        self.assertIsNone(self.store.claim_test_only('P-A','T-1','other',11,20,2))
    def test_wrong_revision_denied(self):
        self.assertIsNone(self.store.claim_test_only('P-A','T-1','worker',10,20,3))
    def test_reclaim_expired_increments_fence(self):
        self.store.claim_test_only('P-A','T-1','worker',10,5,2)
        self.assertEqual(self.store.claim_test_only('P-A','T-1','other',16,5,2),2)
    def test_stale_completion_denied(self):
        self.store.claim_test_only('P-A','T-1','worker',10,5,2)
        self.store.claim_test_only('P-A','T-1','other',16,5,2)
        with self.assertRaises(LedgerConflict):
            self.store.complete_test_only('P-A','T-1','worker',1,'r','h',17)
    def test_complete(self):
        ep=self.store.claim_test_only('P-A','T-1','worker',10,10,2)
        self.assertEqual(self.store.complete_test_only('P-A','T-1','worker',ep,'r','h',11),'COMMITTED')
    def test_exact_replay(self):
        ep=self.store.claim_test_only('P-A','T-1','worker',10,10,2)
        self.store.complete_test_only('P-A','T-1','worker',ep,'r','h',11)
        self.assertEqual(self.store.complete_test_only('P-A','T-1','worker',ep,'r','h',12),'EXACT_REPLAY')
    def test_conflicting_replay_denied(self):
        ep=self.store.claim_test_only('P-A','T-1','worker',10,10,2)
        self.store.complete_test_only('P-A','T-1','worker',ep,'r','h',11)
        with self.assertRaises(LedgerConflict):
            self.store.complete_test_only('P-A','T-1','worker',ep,'r','evil',12)
    def test_completed_cannot_reclaim(self):
        ep=self.store.claim_test_only('P-A','T-1','worker',10,10,2)
        self.store.complete_test_only('P-A','T-1','worker',ep,'r','h',11)
        self.assertIsNone(self.store.claim_test_only('P-A','T-1','other',50,10,2))
    def test_expired_lease_completion_denied(self):
        ep=self.store.claim_test_only('P-A','T-1','worker',10,10,2)
        with self.assertRaises(LedgerConflict):self.store.complete_test_only('P-A','T-1','worker',ep,'r','h',21)
    def test_wrong_worker_completion_denied(self):
        ep=self.store.claim_test_only('P-A','T-1','worker',10,10,2)
        with self.assertRaises(LedgerConflict):self.store.complete_test_only('P-A','T-1','other',ep,'r','h',11)
    def test_close_reopen_persists(self):
        ep=self.store.claim_test_only('P-A','T-1','worker',10,10,2)
        self.store.close(); self.store=DurableLedger(self.db)
        self.assertEqual(self.store.inspect_test_only('P-A','T-1'),('CLAIMED',ep))
    def test_two_connections_sequential_contention(self):
        other=DurableLedger(self.db)
        try:
            self.assertEqual(self.store.claim_test_only('P-A','T-1','w1',10,10,2),1)
            self.assertIsNone(other.claim_test_only('P-A','T-1','w2',10,10,2))
        finally:other.close()
    def test_project_isolation(self):
        self.store.enqueue_test_only('P-B','T-1',2)
        self.store.claim_test_only('P-A','T-1','worker',10,10,2)
        self.assertEqual(self.store.inspect_test_only('P-B','T-1'),('READY',0))
    def test_atomic_rollback_on_exception(self):
        with self.assertRaises(RuntimeError):
            with self.store.tx():
                self.store.conn.execute('UPDATE jobs SET state=? WHERE project_id=? AND task_id=?',('COMPLETE','P-A','T-1'))
                raise RuntimeError('simulate_failure')
        self.assertEqual(self.store.inspect_test_only('P-A','T-1'),('READY',0))
    def test_invalid_enqueue(self):
        with self.assertRaises(ValueError):self.store.enqueue_test_only('','T',2)
    def test_missing_task_claim_denied(self):
        self.assertIsNone(self.store.claim_test_only('P-A','MISSING','w',10,20,2))
    def test_no_cross_project_receipt(self):
        ep=self.store.claim_test_only('P-A','T-1','worker',10,10,2)
        with self.assertRaises(LedgerConflict):
            self.store.complete_test_only('P-B','T-1','worker',ep,'r','h',11)
