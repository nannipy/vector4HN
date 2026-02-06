import pytest
from src.hn import HNClient

@pytest.mark.asyncio
async def test_fetch_top_stories():
    client = HNClient()
    try:
        stories = await client.fetch_top_stories(limit=5)
        assert len(stories) <= 5
        if stories:
            assert "title" in stories[0]
            assert "id" in stories[0]
    finally:
        await client.close()

@pytest.mark.asyncio
async def test_fetch_item():
    client = HNClient()
    try:
        # Fetch item 1 (the first HN item)
        item = await client.fetch_item(1)
        assert item["id"] == 1
        assert "by" in item
    finally:
        await client.close()
