"""
Loads setup/config.env into os.environ so all setup scripts can read credentials
as environment variables without hardcoding them.

Usage in any setup script:
    import _config  # noqa: F401  (must be first, before reading os.environ)
    import os
    APIKEY = os.environ['SAT_APIKEY']

config.env is gitignored. Copy setup/config.env.template -> setup/config.env
and fill in values from your TechZone reservations before running any script.
"""
import os
from pathlib import Path

_config_path = Path(__file__).parent / "config.env"

if not _config_path.exists():
    raise FileNotFoundError(
        f"\n\nERROR: {_config_path} not found.\n"
        "Copy setup/config.env.template -> setup/config.env and fill in your "
        "TechZone reservation values before running setup scripts.\n"
    )

with open(_config_path) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key and value and key not in os.environ:
            os.environ[key] = value
