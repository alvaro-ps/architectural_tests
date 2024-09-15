"""
Pure Domain code should not contain dependencies to IO modules. The reason for this is
that we would like the data processing separate from the handling of this data to
external entities (files, dbs, the internet...). This helps with modularity and also
with unit testing.

The IO modules should be the ones offering what the Domain requires in terms of data
"""

import ast

from itertools import product
from pathlib import Path
from typing import Iterable, TypeVar

from pytest import mark


ROOT = Path(__file__).parents[2].resolve()

A = TypeVar("A")
B = TypeVar("B")


def iter_statements(domain_module: str, statement_type: type[A]) -> Iterable[A]:
    """Iter statements that subclass the given statement type"""
    path = domain_module.replace(".", "/") + ".py"
    module = ast.parse((ROOT / path).read_text(), filename=Path(path).name)
    yield from filter_subclasses(module.body, statement_type)


def filter_subclasses(statements: list[A], statement_type: type[B]) -> Iterable[B]:
    for statement in statements:
        if isinstance(statement, statement_type):
            yield statement


class DomainImportError:
    def __init__(self, io_module: str, domain_module: str):
        self.io_module = io_module
        self.domain_code_path = domain_module
        self.message = self.generate_message(io_module, domain_module)

    @staticmethod
    def generate_message(io_module: str, path: str):
        return f"""Found domain module `{path}` importing IO module `{io_module}`!
            {__doc__}
            """


class TestDomainCodeDoesNotImportIO:
    DOMAIN_MODULES = {"api.core", "api.predicates", "api.query"}
    IO_MODULES = {"api.file", "api.main"}

    @mark.parametrize("domain_module, io_module", product(DOMAIN_MODULES, IO_MODULES))
    def test_import(self, domain_module: str, io_module: str):
        imports = iter_statements(domain_module, statement_type=ast.Import)

        assert not any(
            imported.name == io_module
            for import_ in imports
            for imported in import_.names
        ), DomainImportError(io_module, domain_module).message

    @mark.parametrize("domain_module, io_module", product(DOMAIN_MODULES, IO_MODULES))
    def test_import_from(self, domain_module: str, io_module: str):
        import_froms = iter_statements(domain_module, statement_type=ast.ImportFrom)

        assert not any(
            imported.module == io_module for imported in import_froms
        ), DomainImportError(io_module, domain_module).message
