"""Pytest configuration for the topdesk_mcp test suite."""

import sys
from types import ModuleType, SimpleNamespace


if "requests" not in sys.modules:  # pragma: no cover - testing support only
    stub = ModuleType("requests")

    def _not_implemented(*args, **kwargs):
        raise NotImplementedError("The real 'requests' library is not available in this environment.")

    stub.get = _not_implemented
    stub.post = _not_implemented
    stub.put = _not_implemented
    stub.delete = _not_implemented
    stub.patch = _not_implemented
    stub.Response = object
    stub.exceptions = SimpleNamespace(RequestException=Exception)

    sys.modules["requests"] = stub


if "markitdown" not in sys.modules:  # pragma: no cover - testing support only
    markitdown_stub = ModuleType("markitdown")

    class MarkItDown:  # pylint: disable=too-few-public-methods
        def __init__(self, *args, **kwargs):  # noqa: D401 - simple stub
            """Stubbed MarkItDown initialiser."""

        def convert(self, *args, **kwargs):  # pragma: no cover - placeholder
            raise NotImplementedError("Document conversion is unavailable in the test environment.")

    markitdown_stub.MarkItDown = MarkItDown
    sys.modules["markitdown"] = markitdown_stub


if "urllib3" not in sys.modules:  # pragma: no cover - testing support only
    urllib3_stub = ModuleType("urllib3")

    class _Exceptions(SimpleNamespace):
        InsecureRequestWarning = Warning

    def disable_warnings(*args, **kwargs):  # noqa: D401 - helper stub
        """Stubbed disable_warnings function."""

    urllib3_stub.exceptions = _Exceptions()
    urllib3_stub.disable_warnings = disable_warnings

    sys.modules["urllib3"] = urllib3_stub


if "fastmcp" not in sys.modules:  # pragma: no cover - testing support only
    fastmcp_stub = ModuleType("fastmcp")

    class FastMCP:  # pylint: disable=too-few-public-methods
        def __init__(self, name):
            self.name = name

        def tool(self, *_args, **_kwargs):
            def decorator(func):
                return func

            return decorator

    fastmcp_stub.FastMCP = FastMCP
    sys.modules["fastmcp"] = fastmcp_stub


if "dotenv" not in sys.modules:  # pragma: no cover - testing support only
    dotenv_stub = ModuleType("dotenv")

    def load_dotenv(*_args, **_kwargs):  # noqa: D401 - simple stub
        """Stub implementation of load_dotenv."""

    dotenv_stub.load_dotenv = load_dotenv
    sys.modules["dotenv"] = dotenv_stub
