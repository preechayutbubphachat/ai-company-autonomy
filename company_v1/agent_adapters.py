"""Five-profile binding in dry-run mode only. No provider calls."""
from .models import CANONICAL_PROFILES

class DispatchDenied(RuntimeError):
    pass

def plan_adapter(profile: str, project_id: str, action: str) -> dict:
    if profile not in CANONICAL_PROFILES or not project_id or not action:
        raise DispatchDenied("INVALID_CANONICAL_PROFILE_OR_SCOPE")
    return {"profile":profile,"project_id":project_id,"action":action,
            "dispatch_allowed":False,"reason":"NONPRODUCTION_SOURCE_CANDIDATE"}

def dispatch_live(*_args, **_kwargs):
    raise DispatchDenied("LIVE_DISPATCH_NOT_IMPLEMENTED")
