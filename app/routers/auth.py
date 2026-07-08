from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, security
from fastapi.security import OAuth2PasswordRequestForm

router=APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/signup",response_model=schemas.UserResponse,status_code=status.HTTP_201_CREATED)
def signup(user_data:schemas.UserCreate, db:Session=Depends(get_db)):
    # Check if user already exists
    existing_user=db.query(models.User).filter(models.User.email==user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Hash the password

    hashed_password=security.hash_password(user_data.password)
    new_user=models.User(email=user_data.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# @router.post("/login",response_model=schemas.Token)
# def login(user_data:schemas.UserCreate, db:Session=Depends(get_db)):
#     user=db.query(models.User).filter(models.User.email==user_data.email).first()
#     if not user or not security.verify_password(user_data.password, user.hashed_password):
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

#     access_token=security.create_access_token(data={"sub":user.email})
#     return {"access_token":access_token, "token_type":"bearer"}

@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.email == form_data.username
    ).first()

    if not user or not security.verify_password(
        form_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    access_token = security.create_access_token(
        data={"sub": str(user.id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }