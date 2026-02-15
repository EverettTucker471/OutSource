from fastapi import FastAPI
from app.database import init_db
from app.controllers import user_controller, auth_controller, me_controller, friend_request_controller, circle_controller, event_controller
import time
from sqlalchemy import text
from app.database import engine
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="OutSource API",
    description="Backend API for OutSource mobile app",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    # This regex matches http://localhost:3000, :50165, :8080, etc.
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_controller.router, prefix="/auth")
app.include_router(user_controller.router, prefix="/users")
app.include_router(me_controller.router)
app.include_router(friend_request_controller.router)
app.include_router(circle_controller.router)
app.include_router(event_controller.router)

@app.on_event("startup")
def startup_event():
    max_retries = 30
    retry_count = 0

    while retry_count < max_retries:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("Database connection successful!")
            break
        except Exception as e:
            retry_count += 1
            print(f"Database connection attempt {retry_count}/{max_retries} failed: {e}")
            if retry_count < max_retries:
                time.sleep(2)
            else:
                raise Exception("Could not connect to database after maximum retries")

    init_db()
    print("Database initialized successfully!")


@app.get("/")
def read_root():
    return {"message": "Welcome to OutSource API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
