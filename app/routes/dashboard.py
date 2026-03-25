from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import RouteGroup
from app.services.dashboard_service import (
    get_groups_with_summary,
    get_price_history,
    format_price_brl,
)

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard_index(request: Request, db: Session = Depends(get_db)):
    groups = get_groups_with_summary(db)
    return templates.TemplateResponse(
        request=request,
        name="dashboard/index.html",
        context={"groups": groups, "format_price_brl": format_price_brl},
    )


@router.get("/groups/{group_id}", response_class=HTMLResponse)
def dashboard_detail(request: Request, group_id: int, db: Session = Depends(get_db)):
    group = db.query(RouteGroup).filter(RouteGroup.id == group_id).first()
    if group is None:
        return HTMLResponse(content="Grupo nao encontrado", status_code=404)

    chart_data = get_price_history(db, group_id)
    return templates.TemplateResponse(
        request=request,
        name="dashboard/detail.html",
        context={"group": group, "chart_data": chart_data},
    )
