from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from enseble import ensemble_predict

# Initialize app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Input model
class InputText(BaseModel):
    text: str
    explain: bool = False

@app.post("/predict")
def predict_endpoint(input: InputText):
    print(f"Received text: {input.text}")
    result = ensemble_predict(input.text, include_explanations=input.explain)
    print(f"Prediction result: {result}")
    return {"result": result}