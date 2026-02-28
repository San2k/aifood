#!/usr/bin/env python3
"""Test Russian-to-English translation for FatSecret search."""

import asyncio
import httpx


BASE_URL = "http://localhost:8000"


async def test_russian_food_entry():
    """Test that Russian food entries get translated and found in FatSecret."""

    test_cases = [
        "съел 2 яйца",
        "100 грамм курицы",
        "банан",
        "гречка варёная 150г"
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        for text in test_cases:
            print(f"\n{'='*60}")
            print(f"Testing: '{text}'")
            print('='*60)

            try:
                response = await client.post(
                    f"{BASE_URL}/v1/ingest",
                    json={
                        "user_id": 123456789,
                        "telegram_id": 123456789,
                        "input_type": "text",
                        "raw_input": text,
                        "message_id": 1
                    }
                )

                print(f"Status: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    reply = result.get("reply_text") or result.get("ai_advice") or "No reply"
                    print(f"Response: {reply[:200]}")

                    # Check if food was found
                    if "Нашел" in reply or "вариантов" in reply:
                        print("✅ Translation working - food found in FatSecret!")
                    elif "Не нашел" in reply:
                        print("❌ Translation might not be working - no results")
                    else:
                        print("ℹ️  Response unclear")
                else:
                    print(f"Error: {response.text}")

            except Exception as e:
                print(f"❌ Error: {e}")

            # Wait between requests
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(test_russian_food_entry())
