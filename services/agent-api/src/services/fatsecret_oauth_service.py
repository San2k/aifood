"""
FatSecret OAuth service for user authorization and token management.
"""

import logging
import base64
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import httpx

from ..config import settings

logger = logging.getLogger(__name__)


class FatSecretOAuthService:
    """Service for FatSecret OAuth 2.0 authorization."""

    def __init__(self):
        self.client_id = settings.FATSECRET_CLIENT_ID
        self.client_secret = settings.FATSECRET_CLIENT_SECRET
        self.redirect_uri = settings.FATSECRET_REDIRECT_URI

        # OAuth URLs
        self.authorize_url = "https://www.fatsecret.com/oauth/authorize"
        self.token_url = "https://oauth.fatsecret.com/connect/token"
        self.profile_url = "https://platform.fatsecret.com/rest/server.api"

        self.timeout = httpx.Timeout(30.0)

    def generate_authorization_url(self, telegram_id: int) -> tuple[str, str]:
        """
        Generate OAuth authorization URL for user.

        Args:
            telegram_id: Telegram user ID (used as state)

        Returns:
            Tuple of (authorization_url, state)
        """
        # Generate state for CSRF protection
        state = f"{telegram_id}_{secrets.token_urlsafe(16)}"

        # Build authorization URL
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "basic premier",  # Request full access
            "state": state
        }

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        auth_url = f"{self.authorize_url}?{query_string}"

        logger.info(f"Generated OAuth URL for telegram_id={telegram_id}")

        return auth_url, state

    async def exchange_code_for_tokens(self, authorization_code: str) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            authorization_code: Authorization code from callback

        Returns:
            Dict with tokens and expiration, or None if error
        """
        # Prepare Basic Auth
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_b64 = base64.b64encode(auth_string.encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.redirect_uri
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.token_url, headers=headers, data=data)
                response.raise_for_status()

                token_data = response.json()

                # Calculate expiration time
                expires_in = token_data.get("expires_in", 86400)  # Default 24 hours
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

                result = {
                    "access_token": token_data.get("access_token"),
                    "refresh_token": token_data.get("refresh_token"),
                    "expires_at": expires_at,
                    "token_type": token_data.get("token_type", "Bearer")
                }

                logger.info("Successfully exchanged code for tokens")
                return result

        except httpx.HTTPError as e:
            logger.error(f"Error exchanging code for tokens: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in token exchange: {e}")
            return None

    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            Dict with new tokens, or None if error
        """
        auth_string = f"{self.client_id}:{self.client_secret}"
        auth_b64 = base64.b64encode(auth_string.encode()).decode()

        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.token_url, headers=headers, data=data)
                response.raise_for_status()

                token_data = response.json()

                expires_in = token_data.get("expires_in", 86400)
                expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

                result = {
                    "access_token": token_data.get("access_token"),
                    "refresh_token": token_data.get("refresh_token", refresh_token),  # May return new refresh token
                    "expires_at": expires_at,
                    "token_type": token_data.get("token_type", "Bearer")
                }

                logger.info("Successfully refreshed access token")
                return result

        except httpx.HTTPError as e:
            logger.error(f"Error refreshing token: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in token refresh: {e}")
            return None

    async def get_user_profile(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile from FatSecret.

        Args:
            access_token: OAuth access token

        Returns:
            User profile dict, or None if error
        """
        params = {
            "method": "profile.get",
            "format": "json"
        }

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.profile_url, params=params, headers=headers)
                response.raise_for_status()

                data = response.json()

                # Check for error in response
                if "error" in data:
                    logger.error(f"FatSecret API error: {data['error']}")
                    return None

                profile = data.get("profile", {})

                logger.info(f"Retrieved FatSecret profile for user_id={profile.get('user_id')}")
                return profile

        except httpx.HTTPError as e:
            logger.error(f"Error getting user profile: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting profile: {e}")
            return None

    async def validate_token(self, access_token: str) -> bool:
        """
        Validate if access token is still valid.

        Args:
            access_token: Access token to validate

        Returns:
            True if valid, False otherwise
        """
        profile = await self.get_user_profile(access_token)
        return profile is not None


# Global service instance
fatsecret_oauth_service = FatSecretOAuthService()
