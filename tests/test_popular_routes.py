"""Estado vazio com rotas populares + template create (Phase 28)."""
import datetime

from app.models import RouteGroup


def test_empty_dashboard_shows_popular_routes(client, test_user):
    """Sem grupos, dashboard mostra 6 rotas populares."""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 200
    html = response.text
    assert "Rotas populares no Brasil" in html
    assert "GRU &rarr; LIS" in html
    assert "GIG &rarr; CDG" in html
    assert "REC &rarr; LIS" in html


def test_create_from_template_creates_group_with_defaults(client, test_user, db):
    """POST /groups/create-from-template com template valido cria grupo."""
    response = client.post(
        "/groups/create-from-template",
        data={"template": "gru-lis"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/groups/" in response.headers["location"]
    assert "/edit" in response.headers["location"]

    group = db.query(RouteGroup).filter(RouteGroup.user_id == test_user.id).first()
    assert group is not None
    assert group.origins == ["GRU"]
    assert group.destinations == ["LIS"]
    assert group.duration_days == 10
    assert group.travel_start > datetime.date.today()


def test_create_from_template_invalid_slug_redirects_to_create(client, test_user):
    """Template invalido redireciona para criacao manual."""
    response = client.post(
        "/groups/create-from-template",
        data={"template": "invalid-slug"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "/groups/create" in response.headers["location"]


def test_create_from_template_unauthenticated_redirects_to_login(unauthenticated_client):
    response = unauthenticated_client.post(
        "/groups/create-from-template",
        data={"template": "gru-lis"},
        follow_redirects=False,
    )
    assert response.status_code in (303, 401)


def test_populated_dashboard_does_not_show_popular_routes(client, test_user, db):
    """Com ao menos 1 grupo, estado vazio nao aparece."""
    from datetime import date
    rg = RouteGroup(
        user_id=test_user.id,
        name="Test",
        origins=["GRU"],
        destinations=["LIS"],
        duration_days=7,
        travel_start=date(2026, 7, 1),
        travel_end=date(2026, 7, 31),
        is_active=True,
    )
    db.add(rg)
    db.commit()

    response = client.get("/", follow_redirects=False)
    assert response.status_code == 200
    assert "Rotas populares no Brasil" not in response.text
