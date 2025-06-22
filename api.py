from fastapi import FastAPI
from pydantic import BaseModel
from enseble import ensemble_predict

app = FastAPI()

class InputText(BaseModel):
    text: str
    explain: bool = False

@app.post("/predict")
def predict_endpoint(input: InputText):
    print(f"Received text: {input.text}")
    result = ensemble_predict(input.text, include_explanations=input.explain)
    print(f"Prediction result: {result}")
    return {"result": result}

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)