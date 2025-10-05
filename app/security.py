# 1. Create utility functions for password hashing using hashlib (avoiding bcrypt issues)
import hashlib
import secrets
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from app.config import settings
from app.models.user import User

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    # Split the stored hash to get salt and hash
    try:
        salt, stored_hash = hashed_password.split(':')
        # Hash the plain password with the same salt
        password_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return stored_hash == password_hash.hex()
    except ValueError:
        return False

def get_password_hash(password: str) -> str:
    """Generate password hash with salt"""
    # Generate a random salt
    salt = secrets.token_hex(16)
    # Hash the password with the salt
    password_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    # Return salt:hash format
    return f"{salt}:{password_hash.hex()}"


# 2. Create a utility function for creating JWTs using python-jose
def create_access_token(data: dict) -> str:
    """
    Create access token using JWT
    Uses secret key and HS256 algorithm from settings, includes expiration time
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


# 3. Create a FastAPI dependency function to secure endpoints
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    FastAPI dependency function to secure endpoints
    Decodes JWT from Authorization header, handles errors, extracts username,
    fetches user from MongoDB database using Beanie, and returns user document
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Fetch user from MongoDB database using Beanie
    user = await User.find_one(User.username == username)
    if user is None:
        raise credentials_exception
    
    return user