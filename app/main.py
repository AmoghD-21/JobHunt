from fastapi import FastAPI,Depends,HTTPException,status
from fastapi.middleware.cors import CORSMiddleware
import jwt
from fastapi.security import OAuth2PasswordBearer
from app.database import init_db
from app.routers import auth
from app.config import settings

app=FastAPI(
    title="Jobflow for AI Engine",
    description="A FastAPI application for managing AI engine jobs and workflows.",
    version="1.0.0",
)

init_db()  # Initialize the database and create tables

app.include_router(auth.router)

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return int(user_id)
    except jwt.PyJWTError:
        raise credentials_exception
    

@app.get("/health",tags=["System Operations"])
def health_check():
    return {"status": "ok", "message": "The application is running smoothly."}

@app.get("/users/me", tags=["Secure Test Endqoint"])
def read_users_me(user_id: int = Depends(get_current_user_id)):
    return {"user_id": user_id}