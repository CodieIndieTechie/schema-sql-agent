#!/usr/bin/env python3
"""
Authentication Service for Multi-Tenant SQL Agent

Handles Google OAuth authentication, JWT token management, and user sessions.
"""

import os
import jwt
import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.auth.transport import requests
from google.oauth2 import id_token
import hashlib
import re

from settings import settings


security = HTTPBearer()


class User:
    """Represents an authenticated user."""
    
    def __init__(self, email: str, name: str, picture: str = None):
        self.email = email
        self.name = name
        self.picture = picture
        self.database_name = self.generate_database_name()
        self.created_at = datetime.now()
    
    def generate_database_name(self) -> str:
        """Generate a database name from email address."""
        # Clean email for database naming
        clean_email = re.sub(r'[^a-zA-Z0-9]', '_', self.email.lower())
        
        # Ensure it starts with a letter and is not too long
        if clean_email[0].isdigit():
            clean_email = f"user_{clean_email}"
        
        # Limit length for PostgreSQL
        if len(clean_email) > 50:
            # Use a hash to shorten while keeping it unique
            email_hash = hashlib.md5(self.email.encode()).hexdigest()[:8]
            clean_email = f"user_{email_hash}"
        
        return f"user_{clean_email}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary for JWT payload."""
        return {
            "email": self.email,
            "name": self.name,
            "picture": self.picture,
            "database_name": self.database_name
        }


class AuthService:
    """Service for handling authentication and JWT tokens."""
    
    def __init__(self):
        self.google_client_id = settings.google_client_id
        self.jwt_secret = settings.jwt_secret_key
        self.jwt_algorithm = settings.jwt_algorithm
        self.token_expire_minutes = settings.jwt_access_token_expire_minutes
    
    def create_access_token(self, user: User) -> str:
        """Create a JWT access token for a user."""
        expire = datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)
        
        payload = {
            "sub": user.email,  # Subject (user identifier)
            "exp": expire,      # Expiration time
            "iat": datetime.utcnow(),  # Issued at
            "user": user.to_dict()
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def verify_token(self, token: str) -> User:
        """Verify a JWT token and return the user."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Check if token is expired
            if datetime.utcnow() > datetime.utcfromtimestamp(payload["exp"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired"
                )
            
            # Extract user data
            user_data = payload.get("user")
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token format"
                )
            
            return User(
                email=user_data["email"],
                name=user_data["name"],
                picture=user_data.get("picture")
            )
            
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
    
    async def verify_google_token(self, id_token_str: str) -> User:
        """Verify a Google ID token and return user information."""
        try:
            # Verify the token with Google
            idinfo = id_token.verify_oauth2_token(
                id_token_str, 
                requests.Request(), 
                self.google_client_id
            )
            
            # Check if the token is issued by Google
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            
            # Extract user information
            email = idinfo.get('email')
            name = idinfo.get('name')
            picture = idinfo.get('picture')
            
            if not email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email not provided by Google"
                )
            
            return User(email=email, name=name, picture=picture)
            
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google token: {str(e)}"
            )
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            "client_id": self.google_client_id,
            "client_secret": settings.google_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.oauth_redirect_uri,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to exchange authorization code"
                )
            
            return response.json()


# Global auth service instance
auth_service = AuthService()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dependency to get the current authenticated user from JWT token."""
    token = credentials.credentials
    return auth_service.verify_token(token)


def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    """Optional dependency to get the current user (for endpoints that work with or without auth)."""
    if not credentials:
        return None
    
    try:
        return auth_service.verify_token(credentials.credentials)
    except HTTPException:
        return None


def email_to_database_name(email: str) -> str:
    """Convert email address to a valid database name."""
    user = User(email=email, name="")
    return user.database_name


if __name__ == "__main__":
    # Test the auth service
    test_user = User(email="test@example.com", name="Test User")
    print(f"User: {test_user.email}")
    print(f"Database: {test_user.database_name}")
    
    auth = AuthService()
    token = auth.create_access_token(test_user)
    print(f"Token: {token}")
    
    verified_user = auth.verify_token(token)
    print(f"Verified: {verified_user.email}")
