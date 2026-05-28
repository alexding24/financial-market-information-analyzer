# 如何生成一个可以发给别人的网页链接

目标：把这个本地工具变成一个公开网页。别人打开链接后，就可以输入股票代码查询。

## 最推荐方式：Streamlit Community Cloud

适合第一版公开使用，最简单。

### 你需要准备

1. 一个 GitHub 账号
2. 一个 Streamlit Community Cloud 账号
3. 这个项目上传到 GitHub

## 步骤 1：把项目放到 GitHub

在 GitHub 新建一个 repository，例如：

```text
financial-market-analyzer
```

然后把当前项目上传到这个 repository。

当前项目文件夹是：

```text
/Users/yufeiding/Documents/financial  market information analyzer
```

## 步骤 2：部署到 Streamlit Cloud

1. 打开 Streamlit Community Cloud
2. 选择 `New app`
3. 选择你的 GitHub repository
4. Main file path 填：

```text
streamlit_app.py
```

5. 点击 Deploy

部署完成后，你会得到一个类似这样的链接：

```text
https://your-app-name.streamlit.app
```

这个链接就可以发给别人。

## 步骤 3：别人怎么使用

别人打开链接后，可以输入：

```text
NVDA
600519
0700
NVDA, AMD, MSFT
```

也可以使用市场选择：

```text
自动识别 / 美股 / A股 / 港股
```

## 关于 OpenAI API Key

当前程序没有 API key 也能运行，会使用内置模板生成报告。

如果你想让报告更像 AI 研究员写的，需要在 Streamlit Cloud 的 Secrets 里添加：

```text
OPENAI_API_KEY="你的 key"
OPENAI_MODEL="gpt-4o-mini"
```

不要把 API key 写进代码，也不要上传到 GitHub。

## 注意事项

- 免费部署适合自己和少量朋友使用
- 数据来自公开数据源，可能有延迟或缺失
- A 股和港股的数据覆盖度取决于 Yahoo Finance
- 自动搜索公开材料对美股更完整，因为可以读取 SEC 文件
- 网页生成的报告保存在云端临时环境里，不一定永久保存

## 备用方式

如果只是临时给朋友看，可以用 ngrok 或 Cloudflare Tunnel 把本地网页临时分享出去。

如果要长期稳定运行，可以部署到：

- Render
- Railway
- Fly.io
- 自己的 VPS

第一版建议先用 Streamlit Community Cloud。
