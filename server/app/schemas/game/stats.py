# app/schemas/game/stats.py
from pydantic import BaseModel


class StatsResponse(BaseModel):
    all_time_high_score: int
    max_combo: int
    total_lines_cleared: int
    total_points: int
