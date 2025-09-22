from typing import Optional
from pydantic import BaseModel


class ForageOut(BaseModel):
    id: int
    x_coord: float
    y_coord: float
    z_coord: float
    teneur: float

    class Config:
        orm_mode = True


class PredictRequest(BaseModel):
    x_coord: float
    y_coord: float
    z_coord: float


class PredictResponse(BaseModel):
    predicted_teneur: float
    model: Optional[str] = None
