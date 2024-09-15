"""
Files containing pure Domain code should not contain dependencies to IO modules

The reason for this is that we would like the data processing separate from the 
handling of this data to external entities (files, dbs, the internet...). This helps
with modularity and also helps for unit testing.

The IO modules should be the ones offering what the Domain requires in terms of data
"""

import ast

from itertools import product
from pathlib import Path
from typing import Iterable, TypeVar

import pytest


ROOT = Path(__file__).parents[2].resolve()

A = TypeVar("A")
B = TypeVar("B")


def iter_statements(path: str, statement_type: type[A]) -> Iterable[A]:
    """Iter statements that subclass the given statement type"""
    module = ast.parse((ROOT / path).read_text(), filename=Path(path).name)
    yield from filter_subclasses(module.body, statement_type)


def filter_subclasses(statements: list[A], statement_type: type[B]) -> Iterable[B]:
    for statement in statements:
        if isinstance(statement, statement_type):
            yield statement


class DomainImportError:
    def __init__(self, io_module: str, domain_code_path: str):
        self.io_module = io_module
        self.domain_code_path = domain_code_path
        self.message = self.generate_message(io_module, domain_code_path)

    @staticmethod
    def generate_message(io_module: str, path: str):
        return f"""Found domain code `{path}` importing IO module `{io_module}`!
            {__doc__}
            """


class TestDomainCodeDoesNotImportIO:
    FILES_WITH_DOMAIN_CODE = {"api/core.py", "api/predicates.py", "api/query.py"}
    IO_MODULES = {"api.file", "api.main"}

    @pytest.mark.parametrize(
        "path, io_module", product(FILES_WITH_DOMAIN_CODE, IO_MODULES)
    )
    def test_import(self, path: str, io_module: str):
        statements = iter_statements(path, statement_type=ast.Import)

        if any(
            imported.name == io_module
            for import_statement in statements
            for imported in import_statement.names
        ):
            pytest.fail(reason=DomainImportError(io_module, path).message)

    @pytest.mark.parametrize(
        "path, io_module", product(FILES_WITH_DOMAIN_CODE, IO_MODULES)
    )
    def test_import_from(self, path: str, io_module: str):
        statements = iter_statements(path, statement_type=ast.ImportFrom)

        if any(
            imported_from
            for imported_from in statements
            if imported_from.module == io_module
        ):
            pytest.fail(reason=DomainImportError(io_module, path).message)
