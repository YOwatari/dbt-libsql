from __future__ import annotations

from typing import TYPE_CHECKING

from dbt.adapters.sql import SQLAdapter
from dbt.adapters.sqlite import SQLiteAdapter
from dbt.adapters.sqlite.relation import SQLiteRelation
from dbt_libsql.adapters.libsql.connections import LibsqlConnectionManager

if TYPE_CHECKING:
    from dbt.adapters.base.relation import BaseRelation


class LibsqlAdapter(SQLiteAdapter):
    ConnectionManager = LibsqlConnectionManager
    Relation = SQLiteRelation

    def drop_schema(self, relation: BaseRelation) -> None:
        SQLAdapter.drop_schema(self, relation)

        if relation.schema != "main" and self.check_schema_exists(str(relation.database), str(relation.schema)):
            self.connections.execute(f"DETACH DATABASE {relation.schema}")
