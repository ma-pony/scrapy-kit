import os
from unittest.mock import ANY, Mock

import pytest
from pytest_twisted import ensureDeferred

from spider_brew_kit.scrapy.pipelines.mongo_pipeline import MongoPipeline


class TestMongoPipeline:
    @pytest.fixture
    def spider(self):
        return Mock()

    @pytest.fixture
    def pipeline(self, mocker):
        os.environ["MONGO_URI"] = "mongodb://localhost:27017"
        os.environ["MONGO_DB_NAME"] = "scrapy"
        connection_pool = {"scrapy": {"results": Mock()}}
        mocker.patch(
            "scrapy_kit.pipelines.mongo.ConnectionPool",
            return_value=connection_pool,
        )
        pipeline = MongoPipeline(
            uri="mongodb://localhost:27017",
            db_name="scrapy",
            collection_name="results"
        )
        return pipeline

    @pytest.fixture
    def item(self):
        return {
            "url": "http://example.com",
            "title": "Test Item",
        }

    @ensureDeferred
    async def test_open_spider(self, spider, pipeline):
        await pipeline.open_spider(spider)
        assert pipeline.collection == pipeline.connection["scrapy"]["results"]

    @ensureDeferred
    async def test_close_spider(self, spider, pipeline):
        pipeline.connection = Mock()
        pipeline.connection.disconnect = Mock()
        await pipeline.close_spider(spider)
        assert pipeline.connection.disconnect.called

    @ensureDeferred
    async def test_upsert_item(self, item, pipeline):
        pipeline.collection = Mock()
        pipeline.collection.find_one = Mock(return_value=None)
        result = await pipeline.upsert_item(item)
        assert result == item
        pipeline.collection.insert_one.assert_called_once_with(
            {**item, "created_at": ANY, "updated_at": ANY}
        )
        collection_item = {"_id": "item_id", "created_at": "2023-01-01 00:00:00"}
        pipeline.collection.find_one = Mock(return_value=collection_item)
        result = await pipeline.upsert_item(item)
        assert result == item
        pipeline.collection.update_one.assert_called_once_with(
            {"_id": collection_item["_id"]},
            {
                "$set": {
                    **item,
                    "created_at": collection_item["created_at"],
                    "updated_at": ANY,
                }
            },
        )

    @ensureDeferred
    async def test_update_item(self, pipeline, item):
        pipeline.collection = Mock()
        pipeline.collection.update_one = Mock(return_value=None)
        await pipeline.update_item(item, None)
        pipeline.collection.update_one.assert_called_once_with(None, {"$set": item})

    @ensureDeferred
    async def test_insert_item(self, pipeline, item):
        pipeline.collection = Mock()
        pipeline.collection.insert_one = Mock(return_value=None)
        await pipeline.insert_item(item)
        pipeline.collection.insert_one.assert_called_once_with(item)

    @ensureDeferred
    async def test_process_item(self, pipeline, item):
        pipeline.collection = Mock()
        pipeline.collection.find_one = Mock(return_value=None)
        result = await pipeline.process_item(item, None)
        assert result == item
