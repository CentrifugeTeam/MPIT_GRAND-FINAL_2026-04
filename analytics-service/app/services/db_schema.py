from sqlalchemy import text
from sqlalchemy.engine import Engine

from app.schemas.analytics import ColumnInfo, TableSchema


def introspect_public(engine: Engine) -> list[TableSchema]:
    sql = text(
        """
        SELECT
            c.table_name,
            c.column_name,
            c.data_type,
            c.udt_name
        FROM information_schema.columns c
        JOIN information_schema.tables t
          ON c.table_schema = t.table_schema
         AND c.table_name = t.table_name
        WHERE c.table_schema = 'public'
          AND t.table_type = 'BASE TABLE'
        ORDER BY c.table_name, c.ordinal_position
        """
    )
    enum_sql = text(
        """
        SELECT
            t.typname::text AS udt_name,
            array_agg(e.enumlabel::text ORDER BY e.enumsortorder) AS labels
        FROM pg_catalog.pg_type t
        JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
        JOIN pg_catalog.pg_enum e ON t.oid = e.enumtypid
        WHERE n.nspname = 'public'
          AND t.typtype = 'e'
        GROUP BY t.typname
        """
    )
    grouped: dict[str, list[ColumnInfo]] = {}
    with engine.connect() as conn:
        rows = conn.execute(sql).mappings().all()
        enum_rows = conn.execute(enum_sql).mappings().all()
    enum_map = {
        str(r["udt_name"]).lower(): list(r["labels"]) for r in enum_rows
    }
    for r in rows:
        tn = r["table_name"]
        dt = r["data_type"]
        udt = r["udt_name"]
        labels = None
        if dt == "USER-DEFINED" and udt and str(udt).lower() in enum_map:
            labels = enum_map[str(udt).lower()]
        grouped.setdefault(tn, []).append(
            ColumnInfo(name=r["column_name"], data_type=dt, enum_values=labels)
        )
    return [
        TableSchema(name=name, columns=cols)
        for name, cols in sorted(grouped.items())
    ]
