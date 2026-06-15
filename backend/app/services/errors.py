"""
Service-layer exceptions.

These let services signal *why* an operation failed without importing FastAPI —
the routers translate them into HTTP status codes. Keeping the mapping at the
edge means the same service can be driven by a script or a test without
dragging the web framework along.
"""


class NotFoundError(Exception):
    """
    The requested resource does not exist, or is not visible to this user.

    Deliberately conflates "missing" with "belongs to someone else": answering
    404 for both means an attacker can't probe for valid ids by watching for a
    403. Routers map this to 404.
    """
