# Create a FastAPI APIRouter for authentication
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.models.user import User, UserCreate, UserResponse, Token
from app.schemas import UserPublic
from app.security import get_password_hash, verify_password, create_access_token, get_current_user

router = APIRouter(tags=["Authentication"])


# 1. Create a POST endpoint at "/register" that takes a `UserCreate` schema
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate):
    """
    Register a new user
    Hash the password, check if user already exists, and save new user to database
    """
    # Check if user already exists
    existing_user_username = await User.find_one(User.username == user_data.username)
    if existing_user_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    existing_user_email = await User.find_one(User.email == user_data.email)
    if existing_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password
    hashed_password = get_password_hash(user_data.password)
    
    # Create and save new user to database
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password
    )
    await new_user.insert()
    
    # Return user data safely (without password)
    return UserResponse(
        id=str(new_user.id),
        email=new_user.email,
        username=new_user.username,
        full_name=new_user.full_name,
        is_active=new_user.is_active,
        created_at=new_user.created_at,
        last_login=new_user.last_login
    )


# 2. Create a POST endpoint at "/login" that accepts OAuth2PasswordRequestForm data
@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login endpoint that accepts OAuth2PasswordRequestForm data
    Find user, verify password, and return JWT access token
    """
    # Find the user in database
    user = await User.find_one(User.username == form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify the password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create and return JWT access token with user data
    access_token = create_access_token(data={"sub": user.username})
    user_data = UserResponse(
        id=str(user.id),
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login
    )
    return Token(access_token=access_token, token_type="bearer", user=user_data)


# 3. Create a GET endpoint at "/me" that returns the current authenticated user
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information
    Protected endpoint that requires valid JWT token
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout endpoint - in a stateless JWT system, logout is handled client-side
    This endpoint can be used for logging purposes or future token blacklisting
    """
    return {"message": "Successfully logged out"}