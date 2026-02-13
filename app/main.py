from fastapi import FastAPI
from app.routers import cv, interview
from app.database import create_db_and_tables

app = FastAPI(title="AR Interview Coach Backend")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    print("Database tables created.")

# router registration
app.include_router(cv.router)
app.include_router(interview.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)