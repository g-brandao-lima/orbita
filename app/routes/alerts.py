from fastapi import APIRouter
from app.services.alert_service import verify_silence_token  # noqa: F401

router = APIRouter()


@router.get("/alerts/silence/{token}")
def silence_group(token: str, group_id: int):
    raise NotImplementedError
