# Financial Market Information Analyzer

一个适合从零开始学习和扩展的金融市场信息分析助手。

第一版功能：

- 输入股票代码，例如 `AAPL`、`NVDA`、`TSLA`
- 支持美股、A 股和港股
- 支持一次输入多个股票代码，例如 `NVDA, AMD, INTC`
- 自动获取公司基本信息和最近股价
- 计算简单指标
- 生成中文分析报告
- 生成多只股票的对比表
- 查看近 1 个月、3 个月、6 个月资金流向估算
- 查看分析师共识评级、覆盖数量和平均目标价
- 根据 earnings call、meeting、10-K 文本分析公司未来动向
- 统计业务关键词在重要场合被提到的次数
- 自动搜索 Yahoo Finance 新闻摘要和 SEC 最近 10-K / 10-Q
- 自动生成买前检查清单
- 自动提取最近季度关键财务表格
- 可选接入 Financial Modeling Prep、Finnhub、Alpha Vantage、EODHD、Twelve Data 免费 API key，补充市值、PE、收入增长、利润率、分析师目标价等字段
- 自动保存历史快照，并和上次报告对比
- 多股票输入时生成股票池 / 行业机会评分排序
- 输入几个字母时，网页会提示可能想搜索的股票代码
- 可用命令行运行，也可以用网页界面运行

## 1. 安装依赖

在当前文件夹打开终端，然后运行：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. 命令行运行

```bash
python app.py NVDA
```

也可以一次分析多个股票：

```bash
python app.py NVDA AMD INTC
```

或者：

```bash
python app.py NVDA,AMD,INTC
```

多个股票会自动生成对比报告和机会评分排序，适合当作 watchlist 或行业股票池来观察。

A 股和港股也可以分析：

```bash
python app.py 600519 --market cn
python app.py 0700 --market hk
python app.py 600519.SS 000858.SZ 0700.HK
```

自动识别时，6 位数字按 A 股处理，4-5 位数字按港股处理。

报告会显示在屏幕上，也会保存到 `reports/` 文件夹。

如果你有 earnings call、meeting、10-K 的文字或摘要，也可以一起分析：

```bash
python app.py NVDA \
  --earnings-call-file data_inputs/nvda_earnings_call.txt \
  --meeting-file data_inputs/nvda_meeting.txt \
  --tenk-file data_inputs/nvda_10k.txt \
  --keywords "AI,data center,cloud,GPU,demand,margin,capex"
```

也可以让程序自动搜索公开材料：

```bash
python app.py NVDA --auto-research
```

## 3. 网页界面运行

```bash
streamlit run streamlit_app.py
```

然后浏览器会打开一个页面，你可以输入股票代码生成报告。

网页里也可以输入多个股票代码：

```text
NVDA, AMD, INTC
```

网页里展开“可选：加入 earnings call、meeting、10-K 业务信号分析”，可以直接粘贴文字或简短总结。

网页里的“自动搜索公开材料”默认打开，会自动读取 Yahoo Finance 新闻摘要和 SEC 最近 10-K / 10-Q。免费公开数据不一定包含完整 earnings call transcript；如果你有更完整的 transcript，仍然可以粘贴进去补充。

网页输入股票代码时，可以只输入几个字母，例如 `nv`，页面会提示类似 `NVDA - NVIDIA Corporation` 的候选项。

网页里可以在“市场”下拉框选择“自动识别 / 美股 / A股 / 港股”。

网页里展开“可选：免费数据源 API key”，可以临时填写：

- `Financial Modeling Prep API key`
- `Finnhub API key`
- `Alpha Vantage API key`
- `EODHD API key`
- `Twelve Data API key`
- 自定义 API URL 模板和自定义 API key

这些 key 用来补充免费公开数据源缺失的字段。不同免费 API 的开放字段和额度不同，所以不能保证每次都拿全，但通常会比只用 Yahoo Finance 更完整。你也可以在同一个区域勾选要使用的数据源，方便测试哪个源更稳定。

每次生成报告时，程序会在 `reports/history/` 里保存一个历史快照。下次再生成同一只股票报告时，会自动比较机会评分、资金流向、分析师共识和关键词次数变化。

## 4. 生成公开链接

如果想把这个工具变成别人也能打开的网页链接，请看：

```text
DEPLOY.md
```

## 5. 可选：接入 OpenAI

如果你想让报告更像研究员写的，可以设置 OpenAI API key：

```bash
export OPENAI_API_KEY="你的 API key"
```

没有 API key 也可以运行，程序会使用内置的基础报告模板。

## 6. 可选：接入免费金融数据 API

如果你想让市值、PE、收入增长、利润率、分析师目标价更完整，可以申请免费 API key，然后设置环境变量：

```bash
export FMP_API_KEY="你的 Financial Modeling Prep key"
export FINNHUB_API_KEY="你的 Finnhub key"
export ALPHA_VANTAGE_API_KEY="你的 Alpha Vantage key"
export EODHD_API_KEY="你的 EODHD key"
export TWELVE_DATA_API_KEY="你的 Twelve Data key"
```

部署到 Streamlit Cloud 时，可以在 `Manage app` 里的 `Secrets` 设置同名 key。也可以先在网页的“可选：免费数据源 API key”里手动填写测试。

也可以限制只使用部分数据源：

```bash
export FREE_DATA_PROVIDERS="fmp,finnhub,alpha_vantage,eodhd,twelve_data"
```

如果你有自己的 API，可以设置：

```bash
export CUSTOM_FINANCIAL_API_URL="https://example.com/api?symbol={symbol}&apikey={api_key}"
export CUSTOM_FINANCIAL_API_KEY="你的自定义 key"
export FREE_DATA_PROVIDERS="custom"
```

## 7. 关于资金流向

当前版本使用公开价格和成交量做估算：

- 股价上涨当天的成交额，近似看作资金流入
- 股价下跌当天的成交额，近似看作资金流出
- 成交量明显高于近 20 日平均成交量的日期，近似看作“大额成交日”
- 其他日期近似看作“普通成交日”

这不是逐笔成交数据，不能等同于真实大单、小单资金流，只适合做趋势观察。

## 项目结构

```text
data/
  stock_data.py          # 获取股票数据
analysis/
  stock_summary.py       # 计算基础指标
  ai_report.py           # 生成中文报告
reports/                 # 保存报告
app.py                   # 命令行入口
streamlit_app.py         # 网页界面
```
