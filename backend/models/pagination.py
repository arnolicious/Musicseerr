from typing import Any


def paginated_response(
    items: list[Any],
    total: int,
    offset: int,
    limit: int,
) -> dict[str, Any]:
    return {"items": items, "total": total, "offset": offset, "limit": limit}
