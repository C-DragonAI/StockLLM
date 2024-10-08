# 目標

以下的 N = 1, 7, 14

- 預測目標：中期 or 隔日沖

預計使用 GPT 或其他方式分析股票的各個面向，例如基本面、市場、技術等等，綜合每個分析結果得到最後「某支股票在 N 天後的股價」

# 執行（推論）

1. 區分各個人類會分析的各個面向
2. 給定一支股票，收集各個面向會看的資料（開發一段程式來收集資料）
3. 每個面向都寫一個 Prompt，讓 GPT 看這些資料，得到每個面向的分析結果（-1 ~ 1 之間的指標，-1 表示在 N 天後會跌，1 表示在 N 天後會漲）
4. 透過一組權重，加權每個指標的分析結果，最終結果就是這支股票會漲 or 會跌

# 訓練（Target: 各面向考量的權重）

因為是用 GPT 所以沒有真正的訓練，嚴格說起來只能稱作迭代學習

1. 收集各個面向的歷史資料（每 N 天預測後 N 天）
2. 各個面向都寫一組 Prompt 讓 GPT 看歷史資料後預測
3. random 一組權重
4. 透過 1 ~ 3 會有一個 GPT 的預測值，所以我們只缺一個 loss function
5. 寫一組 Prompt 讓 GPT 當作 Loss Function，這個 GPT 也會看歷史資料，然後會看到最後的預測結果跟真實結果，然後讓他微調權重（這邊可能要用 accumulate loss，不然怕會一次調整太大）

# 交叉分析

每個 Prompt 感覺都要給定那間公司的基本資訊，例如做什麼的，在哪個國家，什麼產業，之類的，這樣才能透過這些基本資訊跟其他分析面做交叉分析，例如新聞都報AI，如果GPT不知道公司是做AI的話，那要怎麼透過新聞面來預測會漲還是跌，因此有些東西可能要有多種資訊綜合考量。

# 想法

感覺一支股票會訓練一組權重，不同股票感覺考量的點都不一樣

# 模組

- 資料收集者：取得該面向資料，落檔
- 預測模型：將該面向資料透過該面向的 Prompt 分析預測
- Prompt Store，透過 Prompt 製造一個 GPT
- 評估者 -> 給定預測和真實，要給一個反饋
- Trainer -> 整個 Pipeline，收集資料 -> 預測 -> 評估 -> 調整

# 專案初始化

## 步驟

1. 創建 `.env` 文件

在你的項目根目錄下創建一個 `.env` 文件，並添加以下內容：

```
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_DEFAULT_REGION=your_default_region
AWS_OUTPUT_FORMAT=json
```

2. 執行 `make init` 或 `sh sh/init.sh`，會自動安裝 `aws cli` 以及使用 credential 下載數據

```bash
$make init
sh sh/init.sh
Data folder already exists.
Installing AWS CLI on macOS...
AWS CLI already installed.
Configuring AWS CLI...
download: s3://ai-s3-disk/datasets/StocksData/stock_dates.csv to data/stock_dates.csv
download: s3://ai-s3-disk/datasets/StocksData/stock_daily.csv to data/stock_daily.csv
download: s3://ai-s3-disk/datasets/StocksData/stock_daily_v2.csv to data/stock_daily_v2.csv
```
