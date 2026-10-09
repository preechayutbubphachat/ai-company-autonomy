"""Strict project key comparison at every boundary."""
class ProjectScopeError(ValueError):
    pass

def require_scope(expected_project: str, observed_project: str) -> None:
    if (not expected_project or not observed_project
            or expected_project != observed_project):
        raise ProjectScopeError("PROJECT_SCOPE_MISMATCH")
