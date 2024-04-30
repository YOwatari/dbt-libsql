from __future__ import annotations

from contextlib import contextmanager, suppress
from dataclasses import dataclass
from socket import gethostname

import libsql_experimental as libsql  # type: ignore  # noqa: PGH003
from dbt.adapters.base import Credentials
from dbt.adapters.sqlite.connections import SQLiteConnectionManager
from dbt.contracts.connection import Connection, ConnectionState
from dbt.exceptions import DbtDatabaseError, DbtRuntimeError, FailedToConnectError
from dbt.logger import GLOBAL_LOGGER

logger = GLOBAL_LOGGER


@dataclass
class LibsqlCredentials(Credentials):
    sync_url: str
    auth_token: str
    attaches: dict[str, str]

    @property
    def type(self):  # noqa: ANN201
        return "libsql"

    @property
    def unique_field(self):  # noqa: ANN201
        return gethostname()

    def _connection_keys(self):  # noqa: ANN202
        return ["database", "schema", "sync_url", "auth_token", "attaches"]


class LibsqlConnectionManager(SQLiteConnectionManager):
    TYPE = "libsql"

    @classmethod
    def open(cls, connection: Connection) -> Connection:
        if connection.state == "open":
            logger.debug("Connection is already open, skipping open.")
            return connection

        credentials: LibsqlCredentials = connection.credentials

        attaches: dict[str, str] = {}
        for name, database_id in credentials.attaches.items():
            attaches[name] = database_id

        try:
            handle: libsql.Connection = libsql.connect(
                database="main",
                sync_url=credentials.sync_url,
                auth_token=credentials.auth_token,
            )

            cursor = handle.cursor()
            for name, database_id in attaches.items():
                cursor.execute(f"ATTACH '{database_id}' AS '{name}'")

            connection.state = ConnectionState.OPEN
            connection.handle = handle

            return connection  # noqa: TRY300
        except libsql.Error as e:
            logger.debug("Got an error when attempting to open a connection: %s", str(e))
            connection.handle = None
            connection.state = ConnectionState.FAIL
            raise FailedToConnectError(str(e)) from None
        except Exception as e:
            print(f"Unknown error when attempting to open a connection: {e}")
            raise

    @classmethod
    def get_status(cls, _: libsql.Cursor) -> str:
        return "OK"

    def cancel(self, connection):  # noqa: ANN201, ANN001
        logger.debug("Cancelling queries")
        with suppress(libsql.Error):
            connection.handle.interrupt()
        logger.debug("Queries cancelled")

    @contextmanager
    def exception_handler(self, sql: str):  # noqa: ANN201
        try:
            yield
        except libsql.Error as e:
            self.release()
            logger.debug("libsql error: %s", str(e))
            raise DbtDatabaseError(str(e)) from None
        except Exception as e:  # noqa: BLE001
            logger.debug("Error executing SQL: %s", sql)
            logger.debug("Rolling back transaction.")
            self.release()
            raise DbtRuntimeError(str(e)) from None
