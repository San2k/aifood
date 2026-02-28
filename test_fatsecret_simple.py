#!/usr/bin/env python3
"""Simple test script for FatSecret API."""

import asyncio
import httpx
import base64
import os
from datetime import datetime, timedelta

# Get credentials from environment
CLIENT_ID = os.getenv("FATSECRET_CLIENT_ID")
CLIENT_SECRET = os.getenv("FATSECRET_CLIENT_SECRET")

TOKEN_URL = "https://oauth.fatsecret.com/connect/token"
BASE_URL = "https://platform.fatsecret.com/rest/server.api"

access_token = None
token_expires_at = None


async def get_access_token():
    """Get OAuth token."""
    global access_token, token_expires_at

    if access_token and token_expires_at and datetime.now() < token_expires_at:
        return access_token

    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_b64 = base64.b64encode(auth_string.encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {"grant_type": "client_credentials", "scope": "basic"}

    async with httpx.AsyncClient() as client:
        response = await client.post(TOKEN_URL, headers=headers, data=data, timeout=10.0)
        response.raise_for_status()
        token_data = response.json()

        access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)
        token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)

        return access_token


async def search_foods(query, max_results=10):
    """Search FatSecret API."""
    token = await get_access_token()

    params = {
        "method": "foods.search",
        "search_expression": query,
        "max_results": max_results,
        "page_number": 0,
        "format": "json"
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(BASE_URL, headers=headers, data=params, timeout=10.0)
        response.raise_for_status()
        result = response.json()

        foods_result = result.get("foods", {})
        total_results = foods_result.get("total_results", "0")

        if total_results == "0" or not foods_result.get("food"):
            return []

        food_list = foods_result.get("food", [])
        if isinstance(food_list, dict):
            food_list = [food_list]

        return food_list


async def main():
    """Run tests."""
    queries = [
        "eggs",
        "greek yogurt",
        "high protein yogurt",
        "yogurt protein",
        "banana",
        "chicken breast"
    ]

    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: '{query}'")
        print('='*60)

        try:
            results = await search_foods(query, max_results=5)
            print(f"Found {len(results)} results\n")

            for i, food in enumerate(results, 1):
                name = food.get('food_name', 'N/A')
                brand = food.get('brand_name')
                food_id = food.get('food_id', 'N/A')

                print(f"{i}. {name}")
                if brand:
                    print(f"   Brand: {brand}")
                print(f"   ID: {food_id}")
                print()

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
