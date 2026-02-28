#!/usr/bin/env python3
"""Test FatSecret API with different language parameters."""

import asyncio
import httpx
import base64
import os
import json
from urllib.parse import quote

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


async def test_search_variant(description, params):
    """Test a specific search configuration."""
    token = await get_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    print(f"\n{'='*70}")
    print(f"Test: {description}")
    print(f"{'='*70}")
    print(f"Params: {json.dumps(params, indent=2, ensure_ascii=False)}\n")

    async with httpx.AsyncClient() as client:
        response = await client.post(BASE_URL, headers=headers, data=params, timeout=10.0)

        print(f"Status: {response.status_code}")

        if response.status_code != 200:
            print(f"Error: {response.text}")
            return

        result = response.json()

        # Check for errors
        if "error" in result:
            print(f"API Error: {result['error']}")
            return

        foods_result = result.get("foods", {})
        total = foods_result.get("total_results", "0")
        food_list = foods_result.get("food", [])

        if isinstance(food_list, dict):
            food_list = [food_list]

        print(f"✅ Total results: {total}")
        print(f"✅ Returned: {len(food_list)} items\n")

        if food_list:
            for i, food in enumerate(food_list[:3], 1):
                print(f"{i}. {food.get('food_name')}")
                if food.get('brand_name'):
                    print(f"   Brand: {food['brand_name']}")
                print(f"   ID: {food.get('food_id')}")
                print()


async def main():
    """Test different API configurations."""

    # Test 1: Basic search (what we're doing now)
    await test_search_variant(
        "Basic search - яйца",
        {
            "method": "foods.search",
            "search_expression": "яйца",
            "max_results": "10",
            "page_number": "0",
            "format": "json"
        }
    )

    # Test 2: With language parameter (ru)
    await test_search_variant(
        "With language=ru - яйца",
        {
            "method": "foods.search",
            "search_expression": "яйца",
            "language": "ru",
            "max_results": "10",
            "page_number": "0",
            "format": "json"
        }
    )

    # Test 3: With region parameter
    await test_search_variant(
        "With region=RU - яйца",
        {
            "method": "foods.search",
            "search_expression": "яйца",
            "region": "RU",
            "max_results": "10",
            "page_number": "0",
            "format": "json"
        }
    )

    # Test 4: Both language and region
    await test_search_variant(
        "With language=ru & region=RU - яйца",
        {
            "method": "foods.search",
            "search_expression": "яйца",
            "language": "ru",
            "region": "RU",
            "max_results": "10",
            "page_number": "0",
            "format": "json"
        }
    )

    # Test 5: Try foods.search.v2 method
    await test_search_variant(
        "Method foods.search.v2 - яйца",
        {
            "method": "foods.search.v2",
            "search_expression": "яйца",
            "max_results": "10",
            "page_number": "0",
            "format": "json"
        }
    )

    # Test 6: Try foods.search.v3 method
    await test_search_variant(
        "Method foods.search.v3 - яйца",
        {
            "method": "foods.search.v3",
            "search_expression": "яйца",
            "max_results": "10",
            "page_number": "0",
            "format": "json"
        }
    )

    # Test 7: Check if encoding matters
    await test_search_variant(
        "URL encoded - %D1%8F%D0%B9%D1%86%D0%B0",
        {
            "method": "foods.search",
            "search_expression": quote("яйца"),
            "max_results": "10",
            "page_number": "0",
            "format": "json"
        }
    )

    # Test 8: Different food (курица - chicken)
    await test_search_variant(
        "Different word - курица",
        {
            "method": "foods.search",
            "search_expression": "курица",
            "language": "ru",
            "max_results": "10",
            "page_number": "0",
            "format": "json"
        }
    )


if __name__ == "__main__":
    asyncio.run(main())
