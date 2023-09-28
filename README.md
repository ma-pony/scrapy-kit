# scrapy-kit

A library for scrapy tools, including but not limited to the usual pipelines, middlewares, etc.

## install

```shell
pip install scrapy-kit
```

## usage

### pipelines

#### mongo pipeline

A pipeline saved into MongoDB asynchronously with txmongo

use database
db.createUser(
{
user: "username",
pwd: "password",
roles: [ { role: "readWrite", db: "database" } ]
}
)

how use:

1. add to settings.py

```python
ITEM_PIPELINES = {
    'scrapy_kit.pipelines.MongoPipeline': 300,
}
```

2. add mongo config to settings.py

```python
MONGO_URI = "mongodb://username:password@host:port"
MONGO_DATABASE_NAME = "database"
MONGO_COLLECTION_NAME = "collection"
```

### middlewares

#### proxy connection close middleware

Proxy close connection multiplexing middleware

Tunnel Proxy Dynamic Edition request found that the number of requests in the Personal Centre Tunnel Proxy Usage
Statistics is very small, which is seriously inconsistent with the real number of requests.
Moreover, there is no IP change when using Tunnel Broker Dynamic Edition.
The reason for this is that the tunnel sends requests that reuse previously established connections.
You need to add Connection: close to the header.

How to use it:

1. Add in settings.py:

```python
DOWNLOADER_MIDDLEWARES = {
    'scrapy_kit.middlewares.ProxyConnectionCloseMiddleware': 543,
}

```

## development

```shell
git clone
cd scrapy-kit
poetry install
```
