#!/usr/bin/env python3
"""Debug FatSecret API responses."""

import asyncio
import httpx
import base64
import os
import json
from datetime import datetime, timedelta

CLIENT_ID = os.getenv("FATSECRET_CLIENT_ID")
CLIENT_SECRET = os.getenv("FATSECRET_CLIENT_SECRET")

TOKEN_URL = "https://oauth.fatsecret.com/connect/token"
BASE_URL = "https://platform.fatsecret.com/rest/server.api"


async def get_token():
    """Get OAuth token with debug output."""
    print("Getting OAuth token...")
    print(f"Client ID: {CLIENT_ID[:10]}...")

    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_b64 = base64.b64encode(auth_string.encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {"grant_type": "client_credentials", "scope": "basic"}

    async with httpx.AsyncClient() as client:
        response = await client.post(TOKEN_URL, headers=headers, data=data, timeout=10.0)
        print(f"Token response status: {response.status_code}")

        if response.status_code != 200:
            print(f"Token error: {response.text}")
            return None

        token_data = response.json()
        print("✅ Token obtained successfully")
        return token_data["access_token"]


async def search_debug(query):
    """Search with full debug output."""
    token = await get_token()
    if not token:
        return

    print(f"\n{'='*60}")
    print(f"Searching for: '{query}'")
    print('='*60)

    params = {
        "method": "foods.search",
        "search_expression": query,
        "max_results": "10",
        "page_number": "0",
        "format": "json"
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    print(f"\nRequest params: {json.dumps(params, indent=2)}")

    async with httpx.AsyncClient() as client:
        response = await client.post(BASE_URL, headers=headers, data=params, timeout=10.0)

        print(f"\nResponse status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")

        if response.status_code != 200:
            print(f"Error response: {response.text}")
            return

        result = response.json()
        print(f"\nFull API Response:")
        print(json.dumps(result, indent=2))

        # Parse results
        foods_result = result.get("foods", {})
        total_results = foods_result.get("total_results", "0")
        food_list = foods_result.get("food")

        print(f"\nParsed results:")
        print(f"  total_results: {total_results}")
        print(f"  food list type: {type(food_list)}")
        print(f"  food list length: {len(food_list) if food_list else 0}")


async def main():
    """Run debug tests."""
    await search_debug("egg")


if __name__ == "__main__":
    asyncio.run(main())
