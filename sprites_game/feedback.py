"""Feedback trigger configuration."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

_DATA_PATH = Path(__file__).parent / "data" / "feedbackTrigger.json"

@dataclass
class FeedbackTrigger:
    minutes: int
    emailStages: List[str]


def load_trigger() -> FeedbackTrigger:
    with open(_DATA_PATH, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return FeedbackTrigger(**raw)
