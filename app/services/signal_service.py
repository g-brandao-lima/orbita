from sqlalchemy.orm import Session
from app.models import FlightSnapshot, DetectedSignal


def detect_signals(db: Session, snapshot: FlightSnapshot) -> list[DetectedSignal]:
    """Orquestra deteccao de todos os tipos de sinal para um snapshot."""
    raise NotImplementedError("Plan 02 will implement")
