from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from models import db


def add_column_if_missing(table_name, column_name, ddl):
    """Dodaj SQLite stupac samo ako ga stara baza još nema."""
    columns = {
        row[1]
        for row in db.session.execute(text(f"PRAGMA table_info({table_name})")).all()
    }
    if column_name in columns:
        return

    try:
        db.session.execute(text(ddl))
        db.session.commit()
    except OperationalError as exc:
        db.session.rollback()
        if "duplicate column" not in str(exc).lower():
            raise
