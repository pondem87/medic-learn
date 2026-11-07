"""One-off Fargate bootstrap/migration task; never run in web/worker startup."""

import os
import subprocess
import sys

import psycopg
from psycopg import sql


def main():
    database = os.environ["DATABASE_NAME"]
    username = os.environ["DATABASE_USER"]
    sslmode = os.environ.get("DATABASE_SSL_MODE", "verify-full")
    if sslmode not in {"verify-full", "disable"}:
        raise ValueError("DATABASE_SSL_MODE must be verify-full or disable")
    tls_options = (
        {"sslrootcert": os.environ["DATABASE_SSL_ROOT_CERT"]} if sslmode == "verify-full" else {}
    )
    with psycopg.connect(
        host=os.environ["DATABASE_HOST"],
        dbname=database,
        user=os.environ["DATABASE_ADMIN_USER"],
        password=os.environ["DATABASE_ADMIN_PASSWORD"],
        sslmode=sslmode,
        **tls_options,
        autocommit=True,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", [username])
            if cursor.fetchone() is None:
                cursor.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(username)))
            cursor.execute(
                sql.SQL("ALTER ROLE {} PASSWORD {}").format(
                    sql.Identifier(username), sql.Literal(os.environ["DATABASE_PASSWORD"])
                )
            )
            # Only the application database; no RDS administrator privileges for runtime tasks.
            cursor.execute(
                sql.SQL("GRANT CONNECT, CREATE, TEMPORARY ON DATABASE {} TO {}").format(
                    sql.Identifier(database), sql.Identifier(username)
                )
            )
            cursor.execute(
                sql.SQL("GRANT USAGE, CREATE ON SCHEMA public TO {}").format(
                    sql.Identifier(username)
                )
            )
    os.environ.pop("DATABASE_ADMIN_PASSWORD", None)
    os.environ.pop("DATABASE_ADMIN_USER", None)
    subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"], check=True)


if __name__ == "__main__":
    main()
