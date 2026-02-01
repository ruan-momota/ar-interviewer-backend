from fastapi import FastAPI
from app.routers import cv, interview

app = FastAPI(title="AR Interview Coach Backend")

# router registration
app.include_router(cv.router)
app.include_router(interview.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)