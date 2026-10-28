"""Conservative, transactional removal of accounts without protected activity."""

from sqlalchemy import select

from api.models import Cart, ExternalIdentity, Favorites, Users, db


class UserDeletionBlocked(ValueError):
    pass


_AUXILIARY_TABLES = (ExternalIdentity.__table__, Cart.__table__, Favorites.__table__)


def delete_user_without_history(user, *, session=None):
    session = session or db.session
    try:
        # Lock the account so concurrent deletion attempts cannot both proceed.
        locked = session.execute(
            select(Users).where(Users.id == user.id).with_for_update()
        ).scalar_one_or_none()
        if locked is None:
            raise UserDeletionBlocked("La cuenta ya no existe.")

        for table in db.metadata.tables.values():
            for column in table.columns:
                if not any(fk.column is Users.__table__.c.id for fk in column.foreign_keys):
                    continue
                if table in _AUXILIARY_TABLES:
                    continue
                if session.execute(select(column).where(column == user.id).limit(1)).first():
                    raise UserDeletionBlocked(
                        "La cuenta tiene registros históricos o comerciales y no puede eliminarse."
                    )

        for table in _AUXILIARY_TABLES:
            session.execute(table.delete().where(table.c.get("user_id", table.c.get("usuario_id")) == user.id))
        session.delete(locked)
        session.commit()
    except Exception:
        session.rollback()
        raise
