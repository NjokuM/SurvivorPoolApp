import pytest


@pytest.mark.asyncio
async def test_version_reports_deployed_commit(client, monkeypatch):
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "abc1234")
    res = await client.get("/version")
    assert res.status_code == 200
    assert res.json() == {"commit": "abc1234"}


@pytest.mark.asyncio
async def test_version_without_railway_is_null(client, monkeypatch):
    monkeypatch.delenv("RAILWAY_GIT_COMMIT_SHA", raising=False)
    res = await client.get("/version")
    assert res.json() == {"commit": None}
