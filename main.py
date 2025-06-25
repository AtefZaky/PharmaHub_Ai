from fastapi import FastAPI
from routes import router
import uvicorn

app = FastAPI()

app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)