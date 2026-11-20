"""Role check. STUB: the role comes from an X-Role header, which anyone can set.

Fine for local development. On AWS, replace current_role with a dependency that reads the
role from a verified login token (e.g. a Cognito JWT).
"""
from fastapi import Depends, Header, HTTPException

# role -> access levels it may read
ROLE_ACCESS = {
    "viewer": ["public"],
    "registrar": ["public", "restricted"],
}


def current_role(x_role: str = Header("viewer")) -> str:
    if x_role not in ROLE_ACCESS:
        raise HTTPException(status_code=403, detail=f"unknown role {x_role!r}")
    return x_role


def allowed_levels(role: str) -> list[str]:
    return ROLE_ACCESS[role]


def require_registrar(role: str = Depends(current_role)) -> str:
    if role != "registrar":
        raise HTTPException(status_code=403, detail="only registrar can do this")
    return role
