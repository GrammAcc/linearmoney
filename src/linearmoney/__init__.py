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
    "ext",
]


import logging

# Setup logging
logger = logging.getLogger(__name__)

logger.info("linearmoney root logger initialized.")


from . import cache, data, exceptions, mixins, resources, scalar, vector  # noqa: E402

__version__ = "0.2.1"

CLDR_VERSION = resources.get_package_resource("cldr_version")
