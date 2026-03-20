async def fetch_authorization(_authorization: str = "") -> bool:
    """Authentication disabled: always return True."""
    return True


async def is_authorized(_authorization: str = "") -> dict:
    """Authentication disabled: always return success."""
    return {
        "success": True,
        "message": "Authentication disabled",
    }
