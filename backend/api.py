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

    # Convert numpy types to Python native types
    def convert_numpy_types(obj):
        if isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(item) for item in obj]
        elif hasattr(obj, "item"):  # numpy scalar
            return obj.item()
        elif hasattr(obj, "tolist"):  # numpy array
            return obj.tolist()
        else:
            return obj

    result = convert_numpy_types(result)
    return {"result": result}
