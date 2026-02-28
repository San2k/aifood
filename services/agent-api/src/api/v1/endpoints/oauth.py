"""
OAuth endpoints for FatSecret integration.

NOTE: OAuth 2.0 authorization code flow is NOT supported by FatSecret API.
FatSecret OAuth 2.0 only supports client_credentials (server-to-server).
For user authorization, FatSecret uses OAuth 1.0 three-legged flow.

Current implementation is DISABLED as it's incompatible with FatSecret's actual OAuth support.
See FATSECRET_OAUTH_FINDINGS.md for details.

If user authorization is needed in the future, implement OAuth 1.0 flow instead.
"""

import logging
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

from ....db.session import get_db
from ....db.repositories.user_repository import UserRepository
# from ....services.fatsecret_oauth_service import fatsecret_oauth_service
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# OAUTH 2.0 ENDPOINTS DISABLED
# Reason: FatSecret does not support OAuth 2.0 authorization code flow
# Only client_credentials is supported (server-to-server, no user authorization)
# ============================================================================


# DISABLED: OAuth 2.0 authorization code flow not supported by FatSecret
#
# class OAuthAuthorizeRequest(BaseModel):
#     """Request to get OAuth authorization URL."""
#     telegram_id: int
#
#
# class OAuthAuthorizeResponse(BaseModel):
#     """Response with OAuth authorization URL."""
#     authorization_url: str
#     state: str
#
#
# @router.post("/oauth/fatsecret/authorize", response_model=OAuthAuthorizeResponse)
# async def get_authorization_url(
#     request: OAuthAuthorizeRequest,
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     DISABLED: This endpoint is not functional.
#     FatSecret OAuth 2.0 does not support authorization code flow.
#     """
#     raise HTTPException(
#         status_code=501,
#         detail="FatSecret OAuth 2.0 user authorization not supported. Use manual goal setup via /settings."
#     )


# DISABLED: OAuth callback endpoint - FatSecret will never send authorization codes
#
# @router.get("/oauth/fatsecret/callback")
# async def oauth_callback(
#     code: str = Query(..., description="Authorization code"),
#     state: str = Query(..., description="State parameter"),
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     DISABLED: This endpoint is not functional.
#     FatSecret OAuth 2.0 does not support authorization code flow with callbacks.
#     """
#     error_html = """
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <meta charset="UTF-8">
#         <meta name="viewport" content="width=device-width, initial-scale=1.0">
#         <title>Not Supported</title>
#         <style>
#             body {
#                 font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
#                 display: flex;
#                 justify-content: center;
#                 align-items: center;
#                 min-height: 100vh;
#                 margin: 0;
#                 background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
#                 color: white;
#                 text-align: center;
#                 padding: 20px;
#             }
#             .container {
#                 background: rgba(255, 255, 255, 0.1);
#                 backdrop-filter: blur(10px);
#                 border-radius: 20px;
#                 padding: 40px;
#                 box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
#                 max-width: 500px;
#             }
#             .error-icon {
#                 font-size: 64px;
#                 margin-bottom: 20px;
#             }
#             h1 {
#                 margin: 0 0 20px 0;
#                 font-size: 28px;
#             }
#             p {
#                 font-size: 16px;
#                 line-height: 1.6;
#                 opacity: 0.9;
#             }
#         </style>
#     </head>
#     <body>
#         <div class="container">
#             <div class="error-icon">⚠️</div>
#             <h1>Функция недоступна</h1>
#             <p>Подключение аккаунта FatSecret не поддерживается.</p>
#             <p>Используйте ручную настройку целей через команду /settings в боте.</p>
#             <p><a href="https://t.me/nutraixo_bot" style="color: white;">Открыть бота</a></p>
#         </div>
#     </body>
#     </html>
#     """
#     return HTMLResponse(content=error_html, status_code=501)


# DISABLED: Disconnect endpoint - no user connections supported
#
# @router.post("/oauth/fatsecret/disconnect")
# async def disconnect_fatsecret(
#     telegram_id: int,
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     DISABLED: FatSecret user connections not supported.
#     """
#     raise HTTPException(
#         status_code=501,
#         detail="FatSecret user connections not supported"
#     )


# DISABLED: Sync endpoint - requires user OAuth tokens which are not available
#
# @router.post("/oauth/fatsecret/sync")
# async def sync_fatsecret_data(
#     telegram_id: int,
#     db: AsyncSession = Depends(get_db)
# ):
#     """
#     DISABLED: FatSecret profile sync not supported.
#     OAuth 2.0 does not provide user access tokens.
#     """
#     raise HTTPException(
#         status_code=501,
#         detail="FatSecret profile sync not supported. Use manual goal setup via /settings."
#     )
