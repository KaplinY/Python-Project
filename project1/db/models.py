from pydantic import BaseModel
import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from datetime import datetime

db_meta = sa.MetaData() 

class Base(DeclarativeBase):
    metadata = db_meta 

class Users(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(sa.BigInteger(), primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(sa.String(100), unique=True)
    password: Mapped[str] = mapped_column(sa.Text)
    email: Mapped[str] = mapped_column(sa.Text, unique=True)

class Percents_data(Base):
    __tablename__ = "percents_data"

    id: Mapped[int] = mapped_column(sa.BigInteger(), primary_key=True, autoincrement=True)
    added: Mapped[float] = mapped_column(sa.Float)
    subtracted: Mapped[float] = mapped_column(sa.Float)
    percent: Mapped[float] = mapped_column(sa.Float)
    time: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    user: Mapped[Users] = relationship(Users, foreign_keys=[user_id], uselist=False)