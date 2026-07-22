import os

from datetime import date as date_, datetime

from sqlalchemy import UniqueConstraint, ForeignKey, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

class Base(DeclarativeBase):
    pass

#   Context model (dimension table)
#   id: primary key
#   date: date of this 15-minute window
#   quarter_hour_slot: int 0-95, from time_features.get_quarter_hour_slot()
#   hour_sin, hour_cos, day_of_week, temperature, precipitation,
#     cloud_cover, weather_code: per the .md spec's context feature vector
#   UniqueConstraint(date, quarter_hour_slot) -- enforces "one context row
#     per 15-minute window" at the DB level, so a bug in context_buffer.py
#     that tries to double-insert for the same slot fails loudly instead of
#     silently duplicating rows.
#   https://docs.sqlalchemy.org/en/20/core/constraints.html#unique-constraint

class Context(Base):
    __tablename__ = "context"
    __table_args__ = (
        UniqueConstraint("date", "quarter_hour_slot", name="context_slot"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date_]
    quarter_hour_slot: Mapped[int]
    temperature_2m: Mapped[float]
    cloud_cover: Mapped[float]
    precipitation: Mapped[float]
    weather_code: Mapped[float]
    is_day: Mapped[bool]
    time_sin: Mapped[float]
    time_cos: Mapped[float]
    day_of_week: Mapped[int]


#   Interaction model (fact table)
#   id: primary key
#   track_id, action, weight, timestamp, source, model_version, score:
#     per the .md spec's `interactions` table / feedback_service.Interaction
#   context_id: ForeignKey -> Context.id (many interactions -> one context)
#   https://docs.sqlalchemy.org/en/20/tutorial/orm_related_objects.html
class Interaction(Base):
    __tablename__ = "interaction"

    id: Mapped[int] = mapped_column(primary_key=True)
    track_id: Mapped[str]
    action: Mapped[str]
    weight: Mapped[int]
    timestamp: Mapped[datetime]
    source: Mapped[str]
    model_version: Mapped[str | None]
    score: Mapped[float | None]
    context_id: Mapped[int] = mapped_column(ForeignKey("context.id"))


# Engine/session setup -- SQLite via MUSICBOT_DATABASE_URL (see .env / .md
# spec's config section). Created once at import time, not per-call, since
# building an engine (connection pool) is relatively expensive. Other
# modules (e.g. context_buffer.py) should import SessionLocal from here and
# open their own `with SessionLocal() as session:` block when they have
# actual rows to write.
# https://docs.sqlalchemy.org/en/20/orm/session_basics.html#adding-new-or-existing-items
engine = create_engine(os.environ["MUSICBOT_DATABASE_URL"], echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    Base.metadata.create_all(engine)
