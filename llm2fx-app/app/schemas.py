from pydantic import BaseModel, Field, field_validator
from typing import Literal, List

FxType = Literal["reverb"]  # keep MVP minimal; add "eq" later

BANDS = 12
GAIN_MIN, GAIN_MAX = -12.0, 12.0
DECAY_MIN, DECAY_MAX = 0.2, 6.0

class Text2FxRequest(BaseModel):
    fx_type: FxType
    instrument: str = Field(min_length=1, max_length=30)
    instruction: str = Field(min_length=1, max_length=200)

class ReverbV1(BaseModel):
    gains_db: List[float] = Field(..., min_length=BANDS, max_length=BANDS)
    decays_s: List[float] = Field(..., min_length=BANDS, max_length=BANDS)
    mix: float

    @field_validator("gains_db")
    @classmethod
    def clamp_gains(cls, v: list[float]) -> list[float]:
        return [min(max(x, GAIN_MIN), GAIN_MAX) for x in v]

    @field_validator("decays_s")
    @classmethod
    def clamp_decays(cls, v: list[float]) -> list[float]:
        return [min(max(x, DECAY_MIN), DECAY_MAX) for x in v]

    @field_validator("mix")
    @classmethod
    def clamp_mix(cls, v: float) -> float:
        return min(max(v, 0.0), 1.0)

class Text2FxResponse(BaseModel):
    schema_version: Literal["reverb_v1"]
    reverb: ReverbV1
    reason: str | None = Field(default=None, max_length=280)
