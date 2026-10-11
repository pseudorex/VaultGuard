from fastapi import APIRouter

# Approvals routes are also surfaced under /recovery-requests/{id}/approve
# This router can provide convenience listings if needed.
router = APIRouter(prefix="/approvals", tags=["Approvals"])
