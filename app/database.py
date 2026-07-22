# SQLAlchemy models + session setup, per the .md spec's SQLite + SQLAlchemy
# storage layer. Empty for now -- sketching the two tables whose design was
# just settled (contexts + interactions) so context_buffer.py and
# feedback_service.py have something concrete to target.
#
# TODO: Context model (dimension table)
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
#
# TODO: Interaction model (fact table)
#   id: primary key
#   track_id, action, weight, timestamp, source, model_version, score:
#     per the .md spec's `interactions` table / feedback_service.Interaction
#   context_id: ForeignKey -> Context.id (many interactions -> one context)
#   https://docs.sqlalchemy.org/en/20/tutorial/orm_related_objects.html
#
# TODO: engine/session setup
#   SQLite via MUSICBOT_DATABASE_URL (see .env / .md spec's config section),
#   a sessionmaker, and a bulk-insert-friendly helper (Session.add_all())
#   for context_buffer.py's batched flush.
#   https://docs.sqlalchemy.org/en/20/orm/session_basics.html#adding-new-or-existing-items
