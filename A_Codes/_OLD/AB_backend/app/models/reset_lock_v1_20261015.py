"""The reset lock (plan G1.32; GEN-04, GEN-05).

One row, `lock_id = 1`. A reset claims it at its very start with a single conditional UPDATE, holds it
to its very end, and releases it in a `finally`. "Is a reset running?" is answered by this row and by
nothing else — not by any batch's status, which is what the guard used to infer from until that
inference failed twice (CR-53, TR-65).

The table is deliberately **not** in `reset_service.DELETE_ORDER`: a reset deletes and reloads almost
everything, and the lock must survive the operation it guards. `batch_id` and `acquired_by` are plain
ids with no foreign key for the same reason as `import_batch.uploaded_by` — the rows they would point
at are deleted and reloaded by the reset itself.

Processing state, like a batch status: holding and releasing the lock writes no audit event (the reset
itself is audited, `reset_service._reset_job`).
"""
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ResetLock(Base):
    __tablename__ = "reset_lock"

    lock_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    # The claim token of the reset holding the lock; NULL when the lock is free. Only the holder can
    # release it, so a late or repeated release cannot free someone else's reset.
    holder: Mapped[str | None] = mapped_column(String(40))
    batch_id: Mapped[str | None] = mapped_column(String(40))
    acquired_by: Mapped[str | None] = mapped_column(String(20))
    acquired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # The stage the running reset has reached, or the stage the last one ended at.
    stage: Mapped[str | None] = mapped_column(String(80))
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # How the last reset ended: Completed, Failed or Interrupted; with the stage and reason on failure.
    last_outcome: Mapped[str | None] = mapped_column(String(20))
    last_reason: Mapped[str | None] = mapped_column(Text)
