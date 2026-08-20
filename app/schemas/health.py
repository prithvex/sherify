from typing import Optional
from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    database: str
    version: Optional[str] = "0.1.0"
    app_name: Optional[str] = None
