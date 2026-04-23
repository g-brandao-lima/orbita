import base64
import json

import pytest
from fastapi.testclient import TestClient
from itsdangerous import TimestampSigner
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base, get_db
from app.models import User
from main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _make_session_cookie(data: dict) -> str:
    """Cria um cookie de sessao assinado compativel com SessionMiddleware."""
    payload = base64.b64encode(json.dumps(data).encode("utf-8"))
    signer = TimestampSigner(settings.session_secret_key)
    return signer.sign(payload).decode("utf-8")


@pytest.fixture(autouse=True)
def _reset_flight_cache():
    """Ensure flight_cache is clean between tests to avoid cross-test contamination."""
    from app.services import flight_cache as _fc
    _fc.clear()
    yield
    _fc.clear()


@pytest.fixture(name="db")
def db_fixture():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(name="test_user")
def test_user_fixture(db):
    user = User(
        google_id="google-test-123",
        email="test@gmail.com",
        name="Test User",
        picture_url=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(name="second_user")
def second_user_fixture(db):
    user = User(
        google_id="google-test-456",
        email="other@gmail.com",
        name="Other User",
        picture_url=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(name="unauthenticated_client")
def unauthenticated_client_fixture(db):
    """Client sem sessao - para testar middleware de protecao."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="client")
def client_fixture(db, test_user):
    """Client autenticado por padrao - sessao com user_id do test_user."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    cookie_value = _make_session_cookie({"user_id": test_user.id})
    client.cookies.set("session", cookie_value)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="authenticated_client")
def authenticated_client_fixture(client, test_user):
    from app.auth.dependencies import get_current_user

    app.dependency_overrides[get_current_user] = lambda: test_user
    yield client
    # cleanup: client_fixture already calls dependency_overrides.clear()


@pytest.fixture
def multi_leg_group_factory(db, test_user):
    from app.models import RouteGroup, RouteGroupLeg
    from datetime import date, timedelta

    def _factory(num_legs: int = 2, name: str = "Multi Trip Test"):
        group = RouteGroup(
            user_id=test_user.id,
            name=name,
            origins=["GRU"],
            destinations=["FCO"],
            duration_days=7,
            travel_start=date(2026, 6, 1),
            travel_end=date(2026, 9, 30),
            mode="multi_leg",
            passengers=1,
            is_active=True,
        )
        db.add(group)
        db.flush()
        base_date = date(2026, 6, 1)
        origins = ["GRU", "FCO", "MAD", "LIS", "CDG"]
        destinations = ["FCO", "MAD", "LIS", "CDG", "GRU"]
        for i in range(num_legs):
            leg = RouteGroupLeg(
                route_group_id=group.id,
                order=i + 1,
                origin=origins[i],
                destination=destinations[i],
                window_start=base_date + timedelta(days=i * 20),
                window_end=base_date + timedelta(days=i * 20 + 7),
                min_stay_days=7,
                max_stay_days=14,
            )
            db.add(leg)
        db.commit()
        db.refresh(group)
        return group

    return _factory


@pytest.fixture
def multi_leg_snapshot_factory(db):
    from app.models import FlightSnapshot

    def _factory(group, total_price: float = 6000.0):
        legs = sorted(group.legs, key=lambda l: l.order)
        snapshot = FlightSnapshot(
            route_group_id=group.id,
            origin=legs[0].origin,
            destination=legs[-1].destination,
            departure_date=legs[0].window_start,
            return_date=legs[-1].window_start,
            price=total_price,
            currency="BRL",
            airline="MULTI",
            source="multi_leg",
            details={
                "total_price": total_price,
                "legs": [
                    {
                        "order": leg.order,
                        "origin": leg.origin,
                        "destination": leg.destination,
                        "date": leg.window_start.isoformat(),
                        "price": total_price / len(legs),
                        "airline": "AZ",
                    }
                    for leg in legs
                ],
            },
        )
        db.add(snapshot)
        db.commit()
        db.refresh(snapshot)
        return snapshot

    return _factory
