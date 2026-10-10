"""Offline maker tests; ephemeral Ed25519 keys only."""
import base64
import tempfile
import unittest
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from company_v1.authority_registry import AuthorityRequest,SignedAuthorityVerifier,TestOnlyReplayStore,canonical_bytes
from company_v1.agent_adapters import DispatchDenied,dispatch_live
from company_v1.security import GateSnapshot

class AuthorityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.store=TestOnlyReplayStore(Path(self.tmp.name)/"replay.db")
        self.private=Ed25519PrivateKey.generate()
        self.pub=self.private.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
        self.env=dict(version=1,issuer="OWNER",key_id="key1",audience="AI-COMPANY-AUTONOMY",project_id="P-A",task_id="T1",action="BUILD",revision=2,issued_at=10,not_before=10,expires_at=100,nonce="nonce1")
        self.req=AuthorityRequest("AI-COMPANY-AUTONOMY","P-A","T1","BUILD",2)
    def tearDown(self):
        self.store.close();self.tmp.cleanup()
    def sign(self,e=None,key=None):
        return base64.b64encode((key or self.private).sign(canonical_bytes(e or self.env))).decode()
    def verifier(self,**kw):
        return SignedAuthorityVerifier({("OWNER","key1"):self.pub},self.store,**kw)
    def test_valid_once_then_replay_denied(self):
        v=self.verifier();sig=self.sign()
        self.assertTrue(v.verify_envelope(self.env,sig,self.req,20))
        self.assertFalse(v.verify_envelope(self.env,sig,self.req,20))
    def test_persistent_replay(self):
        self.assertTrue(self.verifier().verify_envelope(self.env,self.sign(),self.req,20))
        self.store.close();self.store=TestOnlyReplayStore(Path(self.tmp.name)/"replay.db")
        self.assertFalse(self.verifier().verify_envelope(self.env,self.sign(),self.req,20))
    def test_tamper_and_wrong_signature(self):
        self.assertFalse(self.verifier().verify_envelope({**self.env,"action":"DELETE"},self.sign(),self.req,20))
        self.assertFalse(self.verifier().verify_envelope(self.env,self.sign(key=Ed25519PrivateKey.generate()),self.req,20))
    def test_unknown_key_and_issuer(self):
        for change in ({"issuer":"UNKNOWN"},{"key_id":"other"}):
            e={**self.env,**change}
            self.assertFalse(self.verifier().verify_envelope(e,self.sign(e),self.req,20))
    def test_revocation(self):
        for kw in ({"revoked_issuers":{"OWNER"}},{"revoked_keys":{("OWNER","key1")}},{"revoked_grants":{("OWNER","P-A","nonce1")}}):
            self.assertFalse(self.verifier(**kw).verify_envelope(self.env,self.sign(),self.req,20))
    def test_wrong_scope(self):
        for req in (AuthorityRequest("OTHER","P-A","T1","BUILD",2),AuthorityRequest("AI-COMPANY-AUTONOMY","P-B","T1","BUILD",2),AuthorityRequest("AI-COMPANY-AUTONOMY","P-A","OTHER","BUILD",2),AuthorityRequest("AI-COMPANY-AUTONOMY","P-A","T1","DELETE",2),AuthorityRequest("AI-COMPANY-AUTONOMY","P-A","T1","BUILD",3)):
            self.assertFalse(self.verifier().verify_envelope(self.env,self.sign(),req,20))
    def test_expiry_future_issued(self):
        for now in (9,100,101):
            self.assertFalse(self.verifier().verify_envelope(self.env,self.sign(),self.req,now))
        e={**self.env,"issued_at":30,"not_before":30}
        self.assertFalse(self.verifier().verify_envelope(e,self.sign(e),self.req,20))
    def test_malformed(self):
        for e in ({**self.env,"extra":"x"},{**self.env,"revision":True},{**self.env,"nonce":""}):
            self.assertFalse(self.verifier().verify_envelope(e,"garbage",self.req,20))
    def test_store_failure(self):
        class Broken:
            def consume(self,*args): raise RuntimeError("unavailable")
        v=SignedAuthorityVerifier({("OWNER","key1"):self.pub},Broken())
        self.assertFalse(v.verify_envelope(self.env,self.sign(),self.req,20))
    def test_key_rotation(self):
        new=Ed25519PrivateKey.generate()
        pub=new.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
        e={**self.env,"key_id":"key2"}
        v=SignedAuthorityVerifier({("OWNER","key2"):pub},self.store,revoked_keys={("OWNER","key1")})
        self.assertFalse(v.verify_envelope(self.env,self.sign(),self.req,20))
        self.assertTrue(v.verify_envelope(e,self.sign(e,new),self.req,20))
    def test_live_execution_stays_denied(self):
        self.assertFalse(GateSnapshot(True,True,True,True).permit_real_execution())
        with self.assertRaises(DispatchDenied):dispatch_live()
