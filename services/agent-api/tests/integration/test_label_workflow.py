"""
Integration tests for label processing workflow.

Tests the complete end-to-end flow:
1. Submit label for processing
2. Poll status
3. Confirm and log to food_log_entry
"""
import pytest
import asyncio
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.asyncio
async def test_label_processing_workflow():
    """Test complete label processing workflow."""

    # Mock photo URL (in real test would be actual label image)
    photo_url = "https://example.com/test-label.jpg"

    async with AsyncClient(base_url="http://localhost:8000") as client:
        # Step 1: Submit label for processing
        response = await client.post(
            "/v1/process_label",
            json={
                "odentity": "test_user",
                "photo_url": photo_url,
                "meal_type": "breakfast",
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert "scan_id" in data
        assert "status" in data
        scan_id = data["scan_id"]

        print(f"✓ Label submitted: scan_id={scan_id}, status={data['status']}")

        # Step 2: Poll for completion (max 30 seconds)
        attempts = 0
        max_attempts = 30
        final_status = data["status"]

        while final_status == "processing" and attempts < max_attempts:
            await asyncio.sleep(1)
            attempts += 1

            status_response = await client.get(f"/v1/scan_status/{scan_id}")
            assert status_response.status_code == 200

            status_data = status_response.json()
            final_status = status_data["status"]

            print(f"  Poll {attempts}: status={final_status}, progress={status_data.get('progress', 0)}%")

        # Step 3: Verify processing completed
        if final_status == "pending_confirmation":
            assert "product" in status_data
            product = status_data["product"]

            print(f"✓ Product recognized: {product['product_name']}")
            print(f"  Calories: {product['nutrition_per_100g']['calories_kcal']} kcal")
            print(f"  Protein: {product['nutrition_per_100g']['protein_g']}g")
            print(f"  Method: {product['extraction_method']}")

            # Step 4: Confirm and log
            confirm_response = await client.post(
                "/v1/confirm_message",
                json={
                    "odentity": "test_user",
                    "message_text": "подтвердить 150г"
                }
            )

            assert confirm_response.status_code == 200
            confirm_data = confirm_response.json()

            assert confirm_data["action"] == "confirm"
            assert "entry_id" in confirm_data

            print(f"✓ Food logged: entry_id={confirm_data['entry_id']}")
            print(f"  Message: {confirm_data['message']}")

        elif final_status == "failed":
            error = status_data.get("error", "Unknown error")
            pytest.fail(f"Label processing failed: {error}")

        else:
            pytest.fail(f"Unexpected status: {final_status}")


@pytest.mark.asyncio
async def test_scan_status_not_found():
    """Test scan status for non-existent scan_id."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get(f"/v1/scan_status/{uuid4()}")

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_confirm_without_pending_scan():
    """Test confirmation when no pending scan exists."""

    async with AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.post(
            "/v1/confirm_message",
            json={
                "odentity": "nonexistent_user",
                "message_text": "подтвердить 150г"
            }
        )

        assert response.status_code == 200
        data = response.json()

        assert data["action"] == "unknown"


@pytest.mark.asyncio
async def test_cancel_scan():
    """Test scan cancellation."""

    photo_url = "https://example.com/test-label.jpg"

    async with AsyncClient(base_url="http://localhost:8000") as client:
        # Submit scan
        response = await client.post(
            "/v1/process_label",
            json={
                "odentity": "test_user_cancel",
                "photo_url": photo_url,
            }
        )

        assert response.status_code == 200
        scan_id = response.json()["scan_id"]

        # Wait for processing
        await asyncio.sleep(2)

        # Cancel
        cancel_response = await client.post(
            "/v1/confirm_message",
            json={
                "odentity": "test_user_cancel",
                "message_text": "отменить"
            }
        )

        assert cancel_response.status_code == 200
        data = cancel_response.json()

        assert data["action"] == "cancel"
        print(f"✓ Scan cancelled: {data['message']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
