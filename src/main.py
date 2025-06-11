from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="My FastAPI Server",
    description="A simple FastAPI server with basic functionality",
    version="0.1.0"
)

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

@app.get("/")
async def root():
    return {"message": "Welcome to the FastAPI Server"}

@app.post("/items/")
async def create_item(item: Item):
    return item
