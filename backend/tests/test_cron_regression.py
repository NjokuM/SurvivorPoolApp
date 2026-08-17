"""
Regression tests for cron job scheduler endpoints and health check.
"""
import os
os.environ["SECRET_KEY"] = "test-secret-key-do-not-use-in-production"
os.environ["CRON_SECRET"] = "test-cron-secret"

import pytest


# ==================== Smart Sync Endpoint ====================

class TestSmartSyncEndpoint:
    @pytest.mark.asyncio
    async def test_smart_sync_post_returns_200(self, client):
        res = await client.post("/external/football/scheduler/smart-sync")
        assert res.status_code == 200

    @pytest.mark.asyncio
    async def test_smart_sync_get_returns_405(self, client):
        """GET should not be accepted — only POST."""
        res = await client.get("/external/football/scheduler/smart-sync")
        assert res.status_code == 405


# ==================== Weekly Refresh Endpoint ====================

class TestWeeklyRefreshEndpoint:
    @pytest.mark.asyncio
    async def test_weekly_refresh_post_returns_200(self, client):
        res = await client.post("/external/football/scheduler/weekly-refresh")
        assert res.status_code == 200

    @pytest.mark.asyncio
    async def test_weekly_refresh_get_returns_405(self, client):
        """GET should not be accepted — only POST."""
        res = await client.get("/external/football/scheduler/weekly-refresh")
        assert res.status_code == 405


# ==================== Response Shape ====================

class TestSchedulerResponseShape:
    @pytest.mark.asyncio
    async def test_smart_sync_returns_expected_fields_no_pools(self, client):
        """With no active pools, should return skipped status."""
        res = await client.post("/external/football/scheduler/smart-sync")
        data = res.json()
        assert "checked_at" in data
        assert "status" in data
        assert data["status"] == "skipped"
        assert data["active_leagues"] == 0

    @pytest.mark.asyncio
    async def test_weekly_refresh_returns_expected_fields_no_pools(self, client):
        """With no active competitions, should return skipped status."""
        res = await client.post("/external/football/scheduler/weekly-refresh")
        data = res.json()
        assert data["status"] == "skipped"
        assert "message" in data
