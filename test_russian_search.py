#!/usr/bin/env python3
"""Test Russian search in FatSecret."""

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
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_b64 = base64.b64encode(auth_string.encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {"grant_type": "client_credentials", "scope": "basic"}

    async with httpx.AsyncClient() as client:
        response = await client.post(TOKEN_URL, headers=headers, data=data, timeout=10.0)
        token_data = response.json()
        return token_data["access_token"]


async def search_debug(query):
    token = await get_token()

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

    print(f"Searching for: '{query}'")

    async with httpx.AsyncClient() as client:
        response = await client.post(BASE_URL, headers=headers, data=params, timeout=10.0)
        result = response.json()

        foods_result = result.get("foods", {})
        total = foods_result.get("total_results", "0")
        food_list = foods_result.get("food", [])

        if isinstance(food_list, dict):
            food_list = [food_list]

        print(f"Total results: {total}")
        print(f"Returned: {len(food_list)} items\n")

        for i, food in enumerate(food_list[:5], 1):
            print(f"{i}. {food.get('food_name')}")
            if food.get('brand_name'):
                print(f"   Brand: {food['brand_name']}")
            print(f"   ID: {food.get('food_id')}")
            print()


async def main():
    # Test Russian word
    await search_debug("яйца")
    print("="*60)

    # Test English equivalent
    await search_debug("eggs")


if __name__ == "__main__":
    asyncio.run(main())
