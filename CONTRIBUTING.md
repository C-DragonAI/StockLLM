## Environment Setup

### Dev Environment

- ubuntu 20.04
- python 3.9

### Dev Setup

```
pip install -r requirements.txt -r requirements-dev.txt
```

```
pre-commit install
```

### 資料存取區 S3 資料夾

s3://ai-s3-disk/datasets/StocksData/

TODO: 到時候新增一個 init.sh 之類的把會用到的資料載進來 ./data