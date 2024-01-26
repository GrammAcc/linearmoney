"""Functions for manipulating package resources."""

from __future__ import annotations


__all__: list[str] = [
    "get_package_resource",
]


import json
import importlib.resources
from os import PathLike
from typing import Literal, Any, TypeAlias

import linearmoney as lm

ResourceName: TypeAlias = (
    Literal["locales"]
    | Literal["currencies"]
    | Literal["supported_iso_codes"]
    | Literal["cldr_version"]
)


def _load_json_resource(res_path: str | PathLike) -> dict:
    with open(res_path, "r") as json_file:
        return json.load(json_file)


def get_package_resource(res_name: ResourceName) -> Any:
    """Load a JSON resource from the package's filesystem.

    Args:
        res_name:
            The name of the resource to load.
    Returns:
        The resource's data as a python structure.
    """

    fn = ".".join([res_name, "json"])
    with importlib.resources.as_file(
        importlib.resources.files(lm).joinpath(fn)
    ) as res_path:
        return _load_json_resource(res_path)
