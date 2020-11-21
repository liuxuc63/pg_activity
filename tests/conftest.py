import asyncio
import threading

import psycopg2
import pytest


@pytest.fixture
def executor(postgresql):
    """Create a thread and return an execute() function that will run SQL queries in that
    thread.
    """
    cnx = []

    loop = asyncio.new_event_loop()

    def execute(query: str, commit: bool = False) -> None:
        def _execute() -> None:
            conn = psycopg2.connect(**postgresql.info.dsn_parameters)
            cnx.append(conn)
            with conn.cursor() as c:
                c.execute(query)
                if commit:
                    conn.commit()

        loop.call_soon_threadsafe(_execute)

    def run_loop() -> None:
        asyncio.set_event_loop(loop)
        loop.run_forever()

    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()

    yield execute

    for conn in cnx:
        loop.call_soon_threadsafe(conn.close)
    loop.call_soon_threadsafe(loop.stop)

    thread.join(timeout=2)
