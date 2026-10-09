"""SQLite synthetic claim/receipt journal. NOT a trusted production store."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

class LedgerConflict(ValueError):
    pass

class DurableLedger:
    def __init__(self, path: str | Path):
        self.conn = sqlite3.connect(str(path), isolation_level=None, timeout=1.0)
        self.conn.execute('PRAGMA busy_timeout=1000')
        self.conn.execute('PRAGMA journal_mode=WAL')
        self.conn.execute('PRAGMA foreign_keys=ON')
        self.conn.executescript("""CREATE TABLE IF NOT EXISTS jobs (
          project_id TEXT NOT NULL,task_id TEXT NOT NULL,state TEXT NOT NULL,
          epoch INTEGER NOT NULL DEFAULT 0, lease_owner TEXT, lease_until INTEGER,
          authority_revision INTEGER NOT NULL, PRIMARY KEY(project_id,task_id));
          CREATE TABLE IF NOT EXISTS receipts (
          project_id TEXT NOT NULL,task_id TEXT NOT NULL,receipt_id TEXT NOT NULL,
          result_hash TEXT NOT NULL,epoch INTEGER NOT NULL,PRIMARY KEY(project_id,task_id));""")

    @contextmanager
    def tx(self):
        self.conn.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.conn.execute('COMMIT')
        except BaseException:
            self.conn.execute('ROLLBACK')
            raise

    def enqueue_test_only(self, project_id: str, task_id: str, authority_revision: int):
        if not project_id or not task_id or authority_revision <= 0:
            raise ValueError('INVALID_TEST_JOB')
        with self.tx():
            self.conn.execute('INSERT INTO jobs(project_id,task_id,state,authority_revision) '
                              'VALUES(?,?,?,?)',(project_id,task_id,'READY',authority_revision))

    def claim_test_only(self, project_id: str, task_id: str, worker_id: str,
                        now: int, lease_seconds: int, expected_revision: int):
        if not worker_id or lease_seconds <= 0 or expected_revision <= 0:
            raise ValueError('INVALID_CLAIM')
        with self.tx():
            row=self.conn.execute('SELECT state,epoch,lease_until,authority_revision '
                'FROM jobs WHERE project_id=? AND task_id=?',(project_id,task_id)).fetchone()
            if row is None or row[3] != expected_revision or row[0]=='COMPLETE':
                return None
            if row[0]=='CLAIMED' and (row[2] is None or row[2] > now):
                return None
            if row[0] not in ('READY','CLAIMED'):
                return None
            new_epoch=row[1]+1
            self.conn.execute('UPDATE jobs SET state=?,epoch=?,lease_owner=?,lease_until=? '
                              'WHERE project_id=? AND task_id=?',
                              ('CLAIMED',new_epoch,worker_id,now+lease_seconds,project_id,task_id))
            return new_epoch

    def complete_test_only(self, project_id: str, task_id: str, worker_id: str,
                           epoch: int, receipt_id: str, result_hash: str, now: int):
        if not (project_id and task_id and worker_id and receipt_id and result_hash) or epoch <= 0:
            raise ValueError('INVALID_COMPLETION')
        with self.tx():
            existing=self.conn.execute('SELECT receipt_id,result_hash,epoch FROM receipts '
                'WHERE project_id=? AND task_id=?',(project_id,task_id)).fetchone()
            if existing is not None:
                if existing == (receipt_id,result_hash,epoch):
                    return 'EXACT_REPLAY'
                raise LedgerConflict('CONFLICTING_RECEIPT')
            row=self.conn.execute('SELECT state,epoch,lease_owner,lease_until FROM jobs '
                'WHERE project_id=? AND task_id=?',(project_id,task_id)).fetchone()
            if (row is None or row[0]!='CLAIMED' or row[1]!=epoch
                    or row[2]!=worker_id or row[3] is None or row[3] <= now):
                raise LedgerConflict('STALE_OR_EXPIRED_FENCE')
            self.conn.execute('INSERT INTO receipts VALUES(?,?,?,?,?)',
                              (project_id,task_id,receipt_id,result_hash,epoch))
            self.conn.execute('UPDATE jobs SET state=? WHERE project_id=? AND task_id=?',
                              ('COMPLETE',project_id,task_id))
            return 'COMMITTED'

    def inspect_test_only(self, project_id: str, task_id: str):
        return self.conn.execute('SELECT state,epoch FROM jobs WHERE project_id=? AND task_id=?',
                                 (project_id,task_id)).fetchone()

    def close(self):
        self.conn.close()
