from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml

from wfintel.paths import CONFIGS


@lru_cache(maxsize=1)
def config() -> dict[str, Any]:
    return dict(yaml.safe_load((CONFIGS / "pipeline.yaml").read_text(encoding="utf-8")))
