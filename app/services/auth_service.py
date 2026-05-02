"""
Authentication Service - Integrates with Backend Supabase Auth
Uses Supabase Auth + user_profiles table from backend
"""

import logging
from typing import Optional, Dict, Any, Tuple
from uuid import UUID
import time
import requests
from jose import jwt
from jose.exceptions import JWTError
from app.database import supabase, supabase_admin
from app.core.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Unified authentication service using Supabase Auth and user_profiles."""
    
    @staticmethod
    def _get_user_db():
        """Get appropriate client for user_profiles operations."""
        # Use service role if available (bypasses RLS), otherwise use anon
        return supabase_admin if supabase_admin else supabase
    
    @staticmethod
    def register_user(
        email: str,
        password: str,
        full_name: str,
        role: str = "student"  # "student", "faculty", "admin"
    ) -> Dict[str, Any]:
        """
        Register a new user with Supabase Auth.
        Creates user in auth.users and syncs to user_profiles table.
        
        Args:
            email: User email
            password: User password
            full_name: User full name
            role: User role (student, faculty, admin)
        
        Returns:
            Dict with access_token, refresh_token, user_id
        
        Raises:
            Exception: If registration fails
        """
        try:
            logger.info(f"🔐 Registering user: {email} as {role}")
            
            # Get appropriate client for user_profiles
            user_db = AuthService._get_user_db()
            
            # 1. Try to check if user already exists in user_profiles
            try:
                existing = user_db.table("user_profiles") \
                    .select("*") \
                    .eq("email", email) \
                    .execute()
                
                if existing.data:
                    logger.warning(f"⚠️ User already exists: {email}")
                    raise Exception(f"User {email} already registered")
            except Exception as check_err:
                # If check fails (RLS issue), just proceed - auth will handle duplicates
                if "already registered" in str(check_err):
                    raise
                logger.warning(f"⚠️ Could not check existing user (continuing): {str(check_err)}")
            
            # 2. Create user in Supabase Auth
            auth_response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name,
                        "role": role
                    }
                }
            })
            
            if not auth_response or not auth_response.user:
                logger.error("Supabase auth failed - no user returned")
                raise Exception("Failed to create user in Supabase Auth")
            
            user_id = auth_response.user.id
            logger.info(f"✓ User created in Supabase Auth: {user_id}")
            
            # 3. Create user profile in user_profiles table (using service role to bypass RLS)
            profile_data = {
                "id": user_id,
                "email": email,
                "full_name": full_name,
                "role": role,
                "is_active": True,
                "features_access": {}  # Can be customized per role later
            }
            
            try:
                user_profile = user_db.table("user_profiles").insert(profile_data).execute()
                logger.info(f"✓ User profile created: {user_id}")
            except Exception as profile_err:
                # If profile creation fails, try update (user might already exist)
                logger.warning(f"Profile insert failed, attempting update: {str(profile_err)}")
                try:
                    user_db.table("user_profiles").update(profile_data).eq("id", user_id).execute()
                    logger.info(f"✓ User profile updated: {user_id}")
                except Exception as update_err:
                    logger.warning(f"Profile update also failed, but continuing: {str(update_err)}")
            
            # 4. Get session token
            session = auth_response.session
            if not session:
                logger.error("No session returned from Supabase")
                raise Exception("Failed to generate session token")
            
            logger.info(f"✅ Registration successful: {email}")
            
            return {
                "status": "success",
                "user_id": str(user_id),
                "email": email,
                "full_name": full_name,
                "role": role,
                "access_token": session.access_token,
                "refresh_token": session.refresh_token or "",
                "token_type": "bearer",
                "expires_in": session.expires_in or 3600
            }
            
        except Exception as e:
            logger.error(f"❌ Registration failed: {str(e)}")
            raise
    
    @staticmethod
    def login_user(email: str, password: str) -> Dict[str, Any]:
        """
        Login user with email and password.
        
        Args:
            email: User email
            password: User password
        
        Returns:
            Dict with access_token, refresh_token, user info
        
        Raises:
            Exception: If login fails
        """
        try:
            logger.info(f"🔐 Login attempt: {email}")
            
            # 1. Authenticate with Supabase Auth
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if not auth_response or not auth_response.user:
                logger.warning(f"Invalid credentials: {email}")
                raise Exception("Invalid email or password")
            
            user_id = auth_response.user.id
            logger.info(f"✓ Authenticated with Supabase: {user_id}")
            
            # 2. Get user profile from user_profiles table (using service role to bypass RLS)
            user_db = AuthService._get_user_db()
            profile = user_db.table("user_profiles") \
                .select("*") \
                .eq("id", user_id) \
                .execute()
            
            if not profile.data:
                logger.warning(f"User profile not found: {user_id}")
                raise Exception("User profile not found")
            
            user_profile = profile.data[0]
            logger.info(f"✓ User profile retrieved: {user_id}")
            
            # 3. Check if user is active
            if not user_profile.get("is_active"):
                logger.warning(f"Inactive user attempted login: {email}")
                raise Exception("User account is inactive")
            
            session = auth_response.session
            if not session:
                logger.error("No session returned")
                raise Exception("Failed to generate session")
            
            logger.info(f"✅ Login successful: {email}")
            
            return {
                "status": "success",
                "user_id": str(user_id),
                "email": user_profile.get("email"),
                "full_name": user_profile.get("full_name"),
                "role": user_profile.get("role", "student"),
                "is_active": user_profile.get("is_active"),
                "access_token": session.access_token,
                "refresh_token": session.refresh_token or "",
                "token_type": "bearer",
                "expires_in": session.expires_in or 3600
            }
            
        except Exception as e:
            logger.error(f"❌ Login failed: {str(e)}")
            raise
    
    @staticmethod
    def verify_token_and_get_user(token: str) -> Dict[str, Any]:
        """
        Verify JWT token and get user profile.
        
        Args:
            token: JWT access token
        
        Returns:
            Dict with user profile info
        
        Raises:
            Exception: If token invalid or user not found
        """
        try:
            logger.info("🔐 Verifying token...")
            
            user_id, claims = AuthService._verify_jwt_offline(token)
            logger.info(f"✓ Token verified (offline): {user_id}")
            
            # 2. Get user profile (using service role to bypass RLS)
            user_db = AuthService._get_user_db()
            user_profile = None
            try:
                profile = user_db.table("user_profiles") \
                    .select("*") \
                    .eq("id", user_id) \
                    .execute()
                if profile.data:
                    user_profile = profile.data[0]
            except Exception as e:
                # If Supabase is temporarily unreachable, fall back to token claims.
                logger.warning(f"⚠️ Could not fetch user profile (falling back to token claims): {str(e)}")

            if user_profile:
                logger.info(f"✅ User verified: {user_id}")
                return {
                    "status": "success",
                    "user_id": str(user_id),
                    "email": user_profile.get("email"),
                    "full_name": user_profile.get("full_name"),
                    "role": user_profile.get("role"),
                    "is_active": user_profile.get("is_active")
                }

            # Fallback (offline): claims are still good for authz decisions.
            app_md = claims.get("app_metadata") or {}
            user_md = claims.get("user_metadata") or {}
            role = app_md.get("role") or user_md.get("role")
            email = claims.get("email") or user_md.get("email")
            full_name = user_md.get("full_name") or user_md.get("name")

            return {
                "status": "success",
                "user_id": str(user_id),
                "email": email,
                "full_name": full_name,
                "role": role,
                "is_active": True
            }
            
        except Exception as e:
            logger.error(f"❌ Token verification failed: {str(e)}")
            raise

    # --------------------------------------------------
    # Offline JWT verification (JWKS cached)
    # --------------------------------------------------
    _jwks_cache: Optional[Dict[str, Any]] = None
    _jwks_cached_at: float = 0.0
    _jwks_ttl_seconds: int = 60 * 60  # 1 hour

    @staticmethod
    def _get_jwks_url() -> str:
        base = (settings.SUPABASE_URL or "").rstrip("/")
        return f"{base}/auth/v1/.well-known/jwks.json"

    @staticmethod
    def _get_jwks(force_refresh: bool = False) -> Dict[str, Any]:
        now = time.time()
        if not force_refresh and AuthService._jwks_cache and (now - AuthService._jwks_cached_at) < AuthService._jwks_ttl_seconds:
            return AuthService._jwks_cache

        url = AuthService._get_jwks_url()
        resp = requests.get(url, timeout=6)
        resp.raise_for_status()
        jwks = resp.json()
        AuthService._jwks_cache = jwks
        AuthService._jwks_cached_at = now
        return jwks

    @staticmethod
    def _verify_jwt_offline(token: str) -> Tuple[str, Dict[str, Any]]:
        """
        Verify Supabase access token offline using JWKS.
        Returns: (user_id, claims)
        """
        try:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            alg = header.get("alg")

            jwks = AuthService._get_jwks(force_refresh=False)
            keys = jwks.get("keys", []) if isinstance(jwks, dict) else []
            key = next((k for k in keys if k.get("kid") == kid), None)
            if not key:
                # Key rotation: refresh once.
                jwks = AuthService._get_jwks(force_refresh=True)
                keys = jwks.get("keys", []) if isinstance(jwks, dict) else []
                key = next((k for k in keys if k.get("kid") == kid), None)
            if not key:
                raise Exception("JWT verification key not found")

            claims = jwt.decode(
                token,
                key,
                algorithms=[alg] if alg else None,
                audience="authenticated",
                options={"verify_at_hash": False},
            )

            user_id = claims.get("sub") or claims.get("user_id")
            if not user_id:
                raise Exception("Token missing user id (sub)")
            return str(user_id), claims

        except JWTError as e:
            raise Exception(f"Invalid token: {str(e)}")
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile by user ID.
        
        Args:
            user_id: UUID of user
        
        Returns:
            User profile dict or None if not found
        """
        try:
            user_db = AuthService._get_user_db()
            profile = user_db.table("user_profiles") \
                .select("*") \
                .eq("id", user_id) \
                .execute()
            
            if not profile.data:
                return None
            
            user_profile = profile.data[0]
            return {
                "user_id": str(user_id),
                "email": user_profile.get("email"),
                "full_name": user_profile.get("full_name"),
                "role": user_profile.get("role"),
                "is_active": user_profile.get("is_active"),
                "created_at": user_profile.get("created_at"),
                "updated_at": user_profile.get("updated_at")
            }
            
        except Exception as e:
            logger.error(f"❌ Error fetching user: {str(e)}")
            return None
