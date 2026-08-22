"""
models.py
Small pydantic models used for request bodies. Kept separate from
main.py just so that file doesn't get too cluttered.
"""

from pydantic import BaseModel


class JobDescriptionIn(BaseModel):
    title: str
    description: str


class MatchRequest(BaseModel):
    candidate_id: int
    job_id: int
