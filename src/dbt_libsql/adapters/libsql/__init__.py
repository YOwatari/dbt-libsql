from dbt.adapters.base import AdapterPlugin
from dbt.include import sqlite
from dbt_libsql.adapters.libsql.connections import LibsqlCredentials
from dbt_libsql.adapters.libsql.impl import LibsqlAdapter

Plugin = AdapterPlugin(
    adapter=LibsqlAdapter,
    credentials=LibsqlCredentials,
    include_path=sqlite.PACKAGE_PATH,
)
