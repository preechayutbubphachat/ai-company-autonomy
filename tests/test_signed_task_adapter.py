"""Signed grants are consumed only for non-live synthetic selection."""
import base64
import tempfile
import unittest
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from company_v1.authority_registry import SignedAuthorityVerifier, TestOnlyReplayStore, canonical_bytes
from company_v1.signed_task_adapter import SignedTaskAuthorityAdapter
from company_v1.company_core import choose
from company_v1.models import Task
from company_v1.agent_adapters import dispatch_live, DispatchDenied

class SignedSelectionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.store=TestOnlyReplayStore(Path(self.temp.name)/"nonce.sqlite")
        self.private=Ed25519PrivateKey.generate()
        pub=self.private.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
        self.verifier=SignedAuthorityVerifier({("owner","key-1"):pub},self.store)
        self.task=Task(project_id="p1",task_id="t1",action="build",priority=1,authority_revision=2,issuer_id="owner",expires_at=100)
        self.env=dict(version=1,issuer="owner",key_id="key-1",audience="AI-COMPANY-AUTONOMY",project_id="p1",task_id="t1",action="build",revision=2,issued_at=10,not_before=10,expires_at=100,nonce="n1")
    def tearDown(self):
        self.store.close();self.temp.cleanup()
    def adapter(self,env=None,task=None):
        env=env if env is not None else self.env
        sig=base64.b64encode(self.private.sign(canonical_bytes(env))).decode()
        return SignedTaskAuthorityAdapter(self.verifier,{((task or self.task).project_id,(task or self.task).task_id):(env,sig)},"AI-COMPANY-AUTONOMY")
    def test_valid_grant_synthetic_only(self):
        result=choose([self.task],20,self.adapter())
        self.assertEqual(result.task,self.task)
        self.assertFalse(result.dispatch_allowed)
        self.assertEqual(choose([self.task],20,self.adapter()).reason,"NO_VERIFIED_ELIGIBLE_TASK")
        with self.assertRaises(DispatchDenied):dispatch_live()
    def test_mismatched_expiry_denied(self):
        from dataclasses import replace
        t=replace(self.task,expires_at=101)
        self.assertIsNone(choose([t],20,self.adapter()).task)
    def test_wrong_project_denied(self):
        from dataclasses import replace
        t=replace(self.task,project_id="p2")
        self.assertIsNone(choose([t],20,self.adapter()).task)
    def test_wrong_issuer_denied(self):
        from dataclasses import replace
        t=replace(self.task,issuer_id="intruder")
        self.assertIsNone(choose([t],20,self.adapter()).task)
    def test_wrong_revision_denied(self):
        from dataclasses import replace
        t=replace(self.task,authority_revision=3)
        self.assertIsNone(choose([t],20,self.adapter()).task)
    def test_owner_hold_denied(self):
        from dataclasses import replace
        t=replace(self.task,owner_required=True)
        self.assertIsNone(choose([t],20,self.adapter()).task)
    def test_missing_grant_denied(self):
        a=SignedTaskAuthorityAdapter(self.verifier,{},"AI-COMPANY-AUTONOMY")
        self.assertIsNone(choose([self.task],20,a).task)
