import os
import logging
from datetime import datetime
from typing import Any, Optional, Union

from scrapy import Item, Spider
from scrapy.exceptions import NotConfigured
from twisted.internet.defer import inlineCallbacks
from txmongo import Database
from txmongo.collection import Collection
from txmongo.connection import ConnectionPool

logger = logging.getLogger(__name__)


class MongoPipeline:
    """
    A pipeline saved into MongoDB asynchronously with txmongo

    use database
    db.createUser(
      {
        user: "username",
        pwd: "password",
        roles: [ { role: "readWrite", db: "database" } ]
      }
    )
    """

    def __init__(
            self, uri: str = None, db_name: str = None, collection_name: str = None
    ):
        """
        初始化
        :param uri:  mongodb://username:password@host:port
        默认从环境变量中获取 MONGO_URI
        :param db_name:  默认从环境变量中获取 MONGO_DB_NAME
        :param collection_name:  默认从环境变量中获取 MONGO_COLLECTION_NAME
        """

        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.connection: ConnectionPool
        self.database: Database
        self.collection: Collection
        if not self.uri or not self.db_name or not self.collection_name:
            raise NotConfigured("No MongoDB configured")

    @classmethod
    def from_crawler(cls, crawler):
        """
        从配置中获取配置信息

        :param crawler:
        :return:
        """
        uri = crawler.settings.get("MONGO_URI") or os.getenv("MONGO_URI")
        db_name = crawler.settings.get("MONGO_DATABASE_NAME") or os.getenv(
            "MONGO_DATABASE_NAME"
        )
        collection_name = (
            crawler.settings.get("MONGO_COLLECTION_NAME") or os.getenv("MONGO_COLLECTION_NAME")
        )
        return cls(
            uri=uri,
            db_name=db_name,
            collection_name=collection_name,
        )

    @inlineCallbacks
    def open_spider(self, spider: Spider):
        """
        spider 启动时触发

        :param spider:
        :type spider: Spider
        :return:
        :rtype:
        """
        self.connection = yield ConnectionPool(self.uri)
        self.database = self.connection[self.db_name]
        self.collection = self.database[self.collection_name]
        logger.info("MongoPipeline is opened")

    @inlineCallbacks
    def close_spider(self, spider: Spider):
        """
        spider 关闭时触发

        :param spider:
        :type spider: Spider
        :return:
        :rtype:
        """
        yield self.connection.disconnect()  # type: ignore

        logger.info("MongoPipeline is closed")

    @inlineCallbacks
    def upsert_item(
            self,
            item: dict[str, Any],
            filters: Optional[Union[list[dict[str, Any]], dict[str, Any]]] = None,
    ):
        """
        更新或插入数据
        先去数据库中查找，如果存在则更新，不存在则插入，
        同时更新 created_at 和 updated_at 字段
        :param item:
        :param filters:
        :return:
        """
        data = yield self.collection.find_one(filters)
        utcnow = datetime.utcnow()
        if data:
            item["created_at"] = (
                data["created_at"] if data.get("created_at") else utcnow
            )
            item["updated_at"] = utcnow
            result = yield self.collection.update_one(
                {"_id": data["_id"]}, {"$set": item}
            )
            logger.info(f"update {filters} item {result} success")
        else:
            item["created_at"] = utcnow
            item["updated_at"] = utcnow
            result = yield self.collection.insert_one(item)
            logger.info(f"create {filters} item {result} success")
        return item

    @inlineCallbacks
    def update_item(self, item: dict[str, Any], filters: dict[str, Any]):
        """
        更新数据
        :param item:
        :param filters:
        :return:
        """
        result = yield self.collection.update_one(filters, {"$set": item})
        logger.info(f"update {filters} item {result} success")

    @inlineCallbacks
    def insert_item(self, item: dict[str, Any]):
        """
        插入数据
        :param item:
        :return:
        """
        result = yield self.collection.insert_one(item)
        logger.info(f"insert item {result} success")

    @inlineCallbacks
    def process_item(self, item: Item, spider: Spider) -> Item:
        """
        处理数据，默认直接插入数据库

        :param item:
        :param spider:
        :return:
        """
        yield self.insert_item(item)
        return item
