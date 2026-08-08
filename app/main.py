from fastapi import FastAPI, HTTPException
from app.models import DeploymentRequest, DeploymentVerdict
from app.agent import evaluate_deployment
import json

app = FastAPI(
    title="Deployment Safety Advisor",
    description="AI-powered deployment safety evaluation for OCI services",
    version="1.0.0"
)

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "deployment-safety-advisor"}

@app.post("/evaluate-deployment", response_model=DeploymentVerdict)
def evaluate(request: DeploymentRequest):
    try:
        verdict = evaluate_deployment(request)
        return verdict
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {
        "service": "Deployment Safety Advisor",
        "docs": "/docs",
        "health": "/health",
        "evaluate": "POST /evaluate-deployment"
    }