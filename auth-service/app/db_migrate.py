"""Startup migrations for role_definitions and users.role column type."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.engine import Engine

SEED_ROLES: list[tuple[str, str, str, bool]] = [
    ("USER", "Пользователь", "Базовая роль", True),
    ("ADMIN", "Администратор", "Полный доступ", True),
    ("PRODUCT_MANAGER", "Product manager", "Роль каталога (guardrails как USER)", False),
    ("DEVELOPER", "Разработчик", "Роль каталога", False),
    ("ANALYST", "Аналитик", "Роль каталога", False),
    ("DATA_ENGINEER", "Data engineer", "Роль каталога", False),
    ("DESIGNER", "Дизайнер", "Роль каталога", False),
    ("QA_ENGINEER", "QA engineer", "Роль каталога", False),
]


def ensure_roles_and_user_column(engine: Engine) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS role_definitions (
                    key VARCHAR(64) PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT,
                    is_system BOOLEAN NOT NULL DEFAULT false,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ
                )
                """
            )
        )
        for key, title, desc, is_sys in SEED_ROLES:
            conn.execute(
                text(
                    """
                    INSERT INTO role_definitions (key, title, description, is_system)
                    VALUES (:key, :title, :desc, :is_sys)
                    ON CONFLICT (key) DO NOTHING
                    """
                ),
                {"key": key, "title": title, "desc": desc, "is_sys": is_sys},
            )

        has_users = conn.execute(
            text(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'users')"
            )
        ).scalar()
        if has_users:
            row = conn.execute(
                text(
                    """
                    SELECT data_type
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'role'
                    """
                )
            ).fetchone()
            if row and row[0] == "USER-DEFINED":
                conn.execute(text("ALTER TABLE users ALTER COLUMN role DROP DEFAULT"))
                conn.execute(
                    text(
                        "ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(64) USING role::text"
                    )
                )
                conn.execute(text("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'USER'"))

            conn.execute(
                text(
                    """
                    UPDATE users SET role = 'USER'
                    WHERE role IS NULL OR role NOT IN (SELECT key FROM role_definitions)
                    """
                )
            )
            conn.execute(
                text(
                    """
                    DO $c$
                    BEGIN
                        ALTER TABLE users
                            ADD CONSTRAINT users_role_fkey
                            FOREIGN KEY (role) REFERENCES role_definitions(key);
                    EXCEPTION
                        WHEN duplicate_object THEN NULL;
                    END $c$;
                    """
                )
            )
