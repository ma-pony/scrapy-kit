# scrapy-kit
A library for scrapy tools, including but not limited to the usual pipelines, middlewares, etc.


## install 
```shell
pip install scrapy-kit
```

## usage

### pipelines
```python
ITEM_PIPELINES = {
    "spider_kit.pipelines.mongo.MongoPipeline": 369,
}
```

## development
```shell
git clone
cd scrapy-kit
poetry install
```
