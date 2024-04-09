"""A library for working with money algebraically."""

from __future__ import annotations

__all__ = [
    "vector",
    "scalar",
    "data",
    "exceptions",
    "resources",
    "mixins",
    "cache",
]


import logging

# Setup logging
logger = logging.getLogger(__name__)

logger.info("linearmoney root logger initialized.")


from . import (  # noqa: E402
    vector,
    cache,
    data,
    exceptions,
    scalar,
    mixins,
    resources,
)

__version__ = "0.1.2"

CLDR_VERSION = resources.get_package_resource("cldr_version")
