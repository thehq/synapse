# -*- coding: utf-8 -*-
# Copyright 2015, 2016 OpenMarket Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import importlib
import platform

from ._base import IncorrectDatabaseSetup
from .postgres import PostgresEngine
from .sqlite import Sqlite3Engine
from .cockroach import CockroachEngine

SUPPORTED_MODULE = {
    "sqlite3": Sqlite3Engine,
    "psycopg2": PostgresEngine,
    "cockroach": CockroachEngine
}


def create_engine(database_config):
    name = database_config["name"]
    engine_class = SUPPORTED_MODULE.get(name, None)

    if engine_class:
        # pypy requires psycopg2cffi rather than psycopg2
        if name == "psycopg2" and platform.python_implementation() == "PyPy":
            name = "psycopg2cffi"
        elif name == "cockroach":
            name = "psycopg2"
        module = importlib.import_module(name)
        return engine_class(module, database_config)

    raise RuntimeError("Unsupported database engine '%s'" % (name,))


__all__ = ["create_engine", "IncorrectDatabaseSetup"]
