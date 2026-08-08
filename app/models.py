from pydantic import BaseModel
from typing import List, Optional

class DeploymentRequest(BaseModel):
    service_id: str
    service_name: str
    version: str
    target_region: str
    deployed_by: str

class AlertInfo(BaseModel):
    id: str
    type: str
    message: str
    fired_at: str

class DeploymentRecord(BaseModel):
    id: str
    version: str
    deployed_at: str
    outcome: str

class DeploymentVerdict(BaseModel):
    verdict: str
    risk_score: int
    reasons: List[str]
    recommended_actions: List[str]
    safe_to_deploy: bool