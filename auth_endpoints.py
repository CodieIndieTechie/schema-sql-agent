#!/usr/bin/env python3
"""
Authentication Endpoints for Multi-Tenant SQL Agent

Provides Google OAuth login, logout, and user management endpoints.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import urllib.parse

from auth_service import auth_service, get_current_user, User
from settings import settings


# Create authentication router
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


class GoogleTokenRequest(BaseModel):
    """Request model for Google ID token verification."""
    id_token: str


class AuthResponse(BaseModel):
    """Response model for successful authentication."""
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class UserResponse(BaseModel):
    """Response model for user information."""
    email: str
    name: str
    picture: Optional[str] = None
    database_name: str


class OAuthCallbackRequest(BaseModel):
    """Request model for OAuth callback."""
    code: str
    state: Optional[str] = None


@auth_router.get("/google/login")
async def google_login():
    """Initiate Google OAuth login flow."""
    # Google OAuth 2.0 authorization URL
    google_auth_url = "https://accounts.google.com/o/oauth2/auth"
    
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.oauth_redirect_uri,
        "scope": "openid email profile",
        "response_type": "code",
        "access_type": "offline",
        "prompt": "select_account"
    }
    
    auth_url = f"{google_auth_url}?{urllib.parse.urlencode(params)}"
    
    # Redirect to Google OAuth instead of returning JSON
    return RedirectResponse(url=auth_url, status_code=302)


@auth_router.post("/google/callback")
async def google_callback(request: OAuthCallbackRequest):
    """Handle Google OAuth callback."""
    if not request.code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided"
        )
    
    try:
        # Exchange authorization code for tokens
        token_data = await auth_service.exchange_code_for_token(request.code)
        
        # Verify the ID token and get user info
        id_token = token_data.get("id_token")
        if not id_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID token not received from Google"
            )
        
        user = await auth_service.verify_google_token(id_token)
        
        # Create our JWT token
        access_token = auth_service.create_access_token(user)
        
        # Return the access token as JSON (for POST requests from frontend)
        return {
            "success": True,
            "access_token": access_token,
            "user": {
                "email": user.email,
                "name": user.name
            }
        }
        
    except Exception as e:
        # Return error as JSON (for POST requests from frontend)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authentication failed: {str(e)}"
        )


@auth_router.post("/google/verify", response_model=AuthResponse)
async def verify_google_token(request: GoogleTokenRequest):
    """Verify a Google ID token directly (for frontend-initiated auth)."""
    user = await auth_service.verify_google_token(request.id_token)
    access_token = auth_service.create_access_token(user)
    
    return AuthResponse(
        access_token=access_token,
        user=user.to_dict()
    )


@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return UserResponse(
        email=current_user.email,
        name=current_user.name,
        picture=current_user.picture,
        database_name=current_user.database_name
    )


@auth_router.post("/logout")
async def logout():
    """Logout endpoint (client should delete token)."""
    return {
        "message": "Logged out successfully. Please delete your access token.",
        "success": True
    }


@auth_router.get("/health")
async def auth_health():
    """Health check endpoint for authentication service."""
    return {
        "status": "healthy",
        "google_client_configured": bool(settings.google_client_id),
        "jwt_configured": bool(settings.jwt_secret_key)
    }


@auth_router.get("/debug/oauth-config")
async def debug_oauth_config():
    """Debug endpoint to check OAuth configuration."""
    return {
        "google_client_id": settings.google_client_id[:20] + "..." if settings.google_client_id else None,
        "google_redirect_uri": settings.oauth_redirect_uri,
        "frontend_host": settings.frontend_host,
        "frontend_port": settings.frontend_port
    }


# Function to include auth router in main app
def include_auth_routes(app):
    """Include authentication routes in the main FastAPI app."""
    app.include_router(auth_router)


if __name__ == "__main__":
    # Test the endpoints
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI(title="Auth Test")
    include_auth_routes(app)
    
    print("Testing auth endpoints at http://localhost:8002")
    print("Visit http://localhost:8002/docs for API documentation")
    uvicorn.run(app, host="0.0.0.0", port=8002)
