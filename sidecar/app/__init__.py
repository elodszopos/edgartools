"""edgar-sidecar: HTTP wrapper around the local edgartools package."""

import os

# Sidecar SEC throttle in requests/sec. edgartools' own default is 9; the sidecar's contract is 8.
DEFAULT_RATE_LIMIT_PER_SEC = 8

# edgartools' HTTP_MGR reads EDGAR_RATE_LIMIT_PER_SEC exactly once, at import, to build its SEC
# request throttle. This package module is imported before app.main / app.routers / app.settings,
# so pinning the value HERE -- ahead of any `from edgar import ...` -- lets edgartools build the
# limiter at the sidecar's rate without reaching into HTTP_MGR internals at runtime. An explicit
# operator value is preserved; load_settings() validates it loudly at boot.
os.environ.setdefault("EDGAR_RATE_LIMIT_PER_SEC", str(DEFAULT_RATE_LIMIT_PER_SEC))
