from sqlalchemy.orm import Session


def get_groups_with_summary(db: Session) -> list[dict]:
    """Return all route groups with cheapest snapshot and most urgent recent signal."""
    raise NotImplementedError


def get_price_history(db: Session, group_id: int, days: int = 14) -> dict:
    """Return price history labels and prices for the cheapest route of a group."""
    raise NotImplementedError


def format_price_brl(price: float) -> str:
    """Format a float price as Brazilian Real string: R$ X.XXX,XX."""
    raise NotImplementedError
