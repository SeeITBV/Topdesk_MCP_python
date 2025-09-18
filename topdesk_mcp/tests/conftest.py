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

    class ListToolsRequest:  # pylint: disable=too-few-public-methods
        """Simple placeholder for FastMCP's ListToolsRequest type."""

        def __init__(self, *args, **kwargs):  # noqa: D401 - placeholder signature
            """Initialise the stub request object."""

    class FastMCP:  # pylint: disable=too-few-public-methods
        def __init__(self, name):
            self.name = name
            self._tools = []
            self._list_tools_handler = None

        def tool(self, *_args, **_kwargs):
            def decorator(func):
                metadata = {
                    "name": _kwargs.get("name", func.__name__),
                    "description": _kwargs.get("description", func.__doc__ or ""),
                }
                setattr(func, "__mcp_tool__", metadata)
                self._tools.append(metadata)
                return func

            return decorator

        def list_tools(self, *_args, **_kwargs):
            def decorator(func):
                self._list_tools_handler = func
                return func

            return decorator

        @property
        def tools(self):  # noqa: D401 - simple stub property
            """Return the list of registered tool metadata."""
            return list(self._tools)

    fastmcp_stub.FastMCP = FastMCP
    fastmcp_stub.ListToolsRequest = ListToolsRequest

    requests_module = ModuleType("fastmcp.requests")
    requests_module.ListToolsRequest = ListToolsRequest

    fastmcp_stub.requests = requests_module

    sys.modules["fastmcp"] = fastmcp_stub
    sys.modules["fastmcp.requests"] = requests_module


if "dotenv" not in sys.modules:  # pragma: no cover - testing support only
    dotenv_stub = ModuleType("dotenv")

    def load_dotenv(*_args, **_kwargs):  # noqa: D401 - simple stub
        """Stub implementation of load_dotenv."""

    dotenv_stub.load_dotenv = load_dotenv
    sys.modules["dotenv"] = dotenv_stub
