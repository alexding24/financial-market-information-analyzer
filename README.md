# Financial Market Information Analyzer

一个适合从零开始学习和扩展的金融市场信息分析助手。

第一版功能：

- 输入股票代码，例如 `AAPL`、`NVDA`、`TSLA`
- 支持一次输入多个股票代码，例如 `NVDA, AMD, INTC`
- 自动获取公司基本信息和最近股价
- 计算简单指标
- 生成中文分析报告
- 生成多只股票的对比表
- 查看近 1 个月、3 个月、6 个月资金流向估算
- 查看分析师共识评级、覆盖数量和平均目标价
- 根据 earnings call、meeting、10-K 文本分析公司未来动向
- 统计业务关键词在重要场合被提到的次数
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

报告会显示在屏幕上，也会保存到 `reports/` 文件夹。

如果你有 earnings call、meeting、10-K 的文字或摘要，也可以一起分析：

```bash
python app.py NVDA \
  --earnings-call-file data_inputs/nvda_earnings_call.txt \
  --meeting-file data_inputs/nvda_meeting.txt \
  --tenk-file data_inputs/nvda_10k.txt \
  --keywords "AI,data center,cloud,GPU,demand,margin,capex"
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

## 4. 可选：接入 OpenAI

如果你想让报告更像研究员写的，可以设置 OpenAI API key：

```bash
export OPENAI_API_KEY="你的 API key"
```

没有 API key 也可以运行，程序会使用内置的基础报告模板。

## 5. 关于资金流向

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
