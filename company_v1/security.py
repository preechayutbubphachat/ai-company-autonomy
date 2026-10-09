"""Runtime gate model; can only deny. No self-promotion."""
from dataclasses import dataclass

@dataclass(frozen=True)
class GateSnapshot:
    lf3_host_accepted: bool = False
    lf4_source_accepted: bool = False
    lf5_store_accepted: bool = False
    a2_confinement_accepted: bool = False

    def permit_real_execution(self) -> bool:
        # Not a production attestation API: hard block regardless of inputs.
        return False

    def reasons(self):
        names=(('LF3',self.lf3_host_accepted),('LF4',self.lf4_source_accepted),
               ('LF5',self.lf5_store_accepted),('A2',self.a2_confinement_accepted))
        return tuple(name for name, accepted in names if not accepted)
