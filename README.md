# Financial Market Information Analyzer

一个适合从零开始学习和扩展的金融市场信息分析助手。

第一版功能：

- 输入股票代码，例如 `AAPL`、`NVDA`、`TSLA`
- 自动获取公司基本信息和最近股价
- 计算简单指标
- 生成中文分析报告
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

报告会显示在屏幕上，也会保存到 `reports/` 文件夹。

## 3. 网页界面运行

```bash
streamlit run streamlit_app.py
```

然后浏览器会打开一个页面，你可以输入股票代码生成报告。

## 4. 可选：接入 OpenAI

如果你想让报告更像研究员写的，可以设置 OpenAI API key：

```bash
export OPENAI_API_KEY="你的 API key"
```

没有 API key 也可以运行，程序会使用内置的基础报告模板。

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
