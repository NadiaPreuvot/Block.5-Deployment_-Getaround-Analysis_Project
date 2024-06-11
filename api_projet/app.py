import mlflow.sklearn
import uvicorn
import pandas as pd 
from pydantic import BaseModel
from fastapi import FastAPI

description = """
Welcome to  GetAround API.  

## Introduction Endpoints

"""
tags_metadata = [
    {
        "name": "Introduction Endpoints",
        "description": "Simple endpoints to try out!",
    },
    {
        "name": "Machine Learning",
        "description": "Prediction price."
    }
]

app = FastAPI(
    title="GetAroundApp",
    description=description,
    version="0.1",
    contact={
        "name": "GetAround",
        "url": APP_URI,
    },
    openapi_tags=tags_metadata
)
class PredictionFeatures(BaseModel):
    model_key: str = "Citroën"
    mileage: int = 140411
    engine_power: int = 100
    fuel: str = "diesel"
    paint_color: str = "black"
    car_type: str = "convertible"
    private_parking_available: bool = True
    has_gps: bool = True
    has_air_conditioning: bool = False
    automatic_car: bool = False
    has_getaround_connect: bool = True
    has_speed_regulator: bool = True
    winter_tires: bool = True

@app.get("/", tags=["Introduction Endpoints"])
async def index():
    """
    This returns a welcome message !
    """
    message = "Hello! This is the default endpoint. You can go to /docs to get an overview of all available endpoints"
    return message

@app.post("/predict", tags=["Machine Learning"])
async def predict(predictionFeatures: PredictionFeatures):
    """
    Prediction du prix à la journée. 
    """
    price_day = pd.DataFrame(dict(predictionFeatures), index=[0])
                            
    logged_model = ''

    # Load model as a PyFuncModel.
    loaded_model = mlflow.pyfunc.load_model(logged_model)

    prediction = loaded_model.predict(price_day)

    response = prediction.tolist()[0]
    
    return response

if __name__=="__main__":
    uvicorn.run(app, host="0.0.0.0", port=4000)