"""Remove all OPD slot timing data (slots, bookings, related meet records)."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import delete

from app.database import AsyncSessionLocal
from app.models import MeetSummary, MeetTranscriptLine, OPDBooking, OPDSlot


async def main() -> None:
    async with AsyncSessionLocal() as db:
        t_lines = await db.execute(delete(MeetTranscriptLine))
        t_summaries = await db.execute(delete(MeetSummary))
        t_bookings = await db.execute(delete(OPDBooking))
        t_slots = await db.execute(delete(OPDSlot))
        await db.commit()
        print(
            f"Cleared OPD data: "
            f"{t_slots.rowcount} slots, "
            f"{t_bookings.rowcount} bookings, "
            f"{t_summaries.rowcount} summaries, "
            f"{t_lines.rowcount} transcript lines"
        )


if __name__ == "__main__":
    asyncio.run(main())
