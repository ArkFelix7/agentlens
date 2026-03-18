# Server utilities package

import uuid as _uuid


def new_ulid() -> str:
    """Generate a new ULID string.

    Handles both 'python-ulid' (python-ulid package, ULID()) and 'ulid-py'
    (ulid-py package, ulid.new()) which both expose an 'ulid' top-level module
    but with incompatible APIs.  Falls back to a UUID4-based hex string if
    neither package works correctly.
    """
    try:
        import ulid as _ulid
        # python-ulid: ULID() with no args returns a new ULID
        obj = _ulid.ULID()
        return str(obj)
    except TypeError:
        # ulid-py is installed and shadows python-ulid — use ulid.new() instead
        try:
            import ulid as _ulid
            return str(_ulid.new())
        except Exception:
            pass
    except Exception:
        pass
    # Final fallback: UUID4 hex (26 chars, same length as ULID)
    return _uuid.uuid4().hex[:26].upper()
