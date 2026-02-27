from pydantic import BaseModel
from model.identity_input import IdentityInput
from model.network_input import NetworkInput
from model.behavioral_input import BehavioralInput

class RiskAssessmentInput(BaseModel):
    identity: IdentityInput
    behavioral: BehavioralInput
    network: NetworkInput