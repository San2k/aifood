#!/usr/bin/env python3
"""
Test script to query FatSecret API directly and see what results are returned.
"""

import asyncio
import sys
import os

# Add the services directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'services/agent-api/src'))

from services.mcp_client import mcp_client


async def test_fatsecret_search(query: str):
    """Test FatSecret API search."""
    print(f"\n{'='*60}")
    print(f"Testing FatSecret API with query: '{query}'")
    print(f"{'='*60}\n")

    try:
        # Search for foods
        results = await mcp_client.search_foods(query, max_results=10)

        print(f"✅ Found {len(results)} results\n")

        if not results:
            print("❌ No results found!")
            return

        # Display results
        for idx, food in enumerate(results, 1):
            print(f"{idx}. {food['food_name']}")
            if food.get('brand_name'):
                print(f"   Brand: {food['brand_name']}")
            print(f"   ID: {food['food_id']}")
            print(f"   Type: {food.get('food_type', 'N/A')}")
            print()

        # Get detailed info for first result
        if results:
            print(f"\n{'='*60}")
            print(f"Getting detailed info for: {results[0]['food_name']}")
            print(f"{'='*60}\n")

            food_id = results[0]['food_id']
            servings = await mcp_client.get_servings(food_id)

            print(f"✅ Found {len(servings)} serving options\n")

            for idx, serving in enumerate(servings[:5], 1):  # Show first 5
                print(f"{idx}. {serving['serving_description']}")
                print(f"   Calories: {serving['calories']} kcal")
                print(f"   Protein: {serving['protein']}g")
                print(f"   Carbs: {serving['carbohydrate']}g")
                print(f"   Fat: {serving['fat']}g")
                if serving.get('metric_serving_amount'):
                    print(f"   Metric: {serving['metric_serving_amount']} {serving.get('metric_serving_unit', '')}")
                print()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run multiple test queries."""

    # Test queries
    test_queries = [
        "eggs",           # Simple English
        "яйца",          # Russian (Cyrillic)
        "greek yogurt",  # Common product
        "banana",        # Fruit
        "chicken breast" # Common protein
    ]

    for query in test_queries:
        await test_fatsecret_search(query)
        print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
