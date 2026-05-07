# 交易助手网站

本项目是基于根目录 `我的交易系统V1.md` 的本地 A 股规则分析原型。

第一版只做规则辅助分析，不做自动交易，不做实盘下单。

## 运行

```bash
pip install -r requirements.txt
python run_server.py
```

访问：

```text
http://127.0.0.1:8000
```

线上服务器默认监听：

```text
http://0.0.0.0:8000
```

也可以通过环境变量指定：

```bash
HOST=0.0.0.0 PORT=8000 python run_server.py
```

## 后台运行

推荐用 systemd 托管服务。

创建服务文件：

```bash
sudo nano /etc/systemd/system/trading-assistant.service
```

写入：

```ini
[Unit]
Description=Trading Assistant FastAPI
After=network.target

[Service]
WorkingDirectory=/opt/trading_assistant
ExecStart=/opt/trading_assistant/.venv/bin/python run_server.py
Restart=always
RestartSec=5
User=root
Environment=HOST=0.0.0.0
Environment=PORT=8000
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

启动并设置开机自启：

```bash
sudo systemctl daemon-reload
sudo systemctl enable trading-assistant
sudo systemctl start trading-assistant
```

查看状态：

```bash
sudo systemctl status trading-assistant
```

查看实时日志：

```bash
journalctl -u trading-assistant -f
```

重启服务：

```bash
sudo systemctl restart trading-assistant
```

停止服务：

```bash
sudo systemctl stop trading-assistant
```

取消开机自启：

```bash
sudo systemctl disable trading-assistant
```

## 当前版本

- 已接入 BaoStock 日 K 数据，作为当前主数据源。
- 已保留 AKShare 日 K 数据作为备用源。
- 已计算 MA5、MA13、MA20、成交量均线。
- 已实现第一版规则判断，并在结果页展示规则检查清单。
- 已实现首页输入、当前用户历史查询、本地股票名称缓存和结果页展示。
- 结果页已加入基础数据、正向条件、风险条件、观察项、操作计划、日 K 与均线示意图。
- 已新增交易系统准则页面 `/rules`，内容从根目录 `我的交易系统V1.md` 读取并以左侧目录、右侧内容方式展示。
- 已新增 520 战法详解页面 `/strategy/520`，内容从交易系统目录下的 Markdown 文档提取并归类展示。

## 当前限制

- 第一版只做日线级规则分析。
- 股票名称通过免费公开接口补全并做本地缓存，接口失败时会回退显示代码。
- AKShare 当前使用的日 K 函数依赖东方财富接口，可能遇到风控、验证码、代理断开等问题，因此已降级为备用源。
- 免费公开数据可能存在延迟、接口变动或拉取失败。
- 大盘、板块、题材、龙虎榜、资金流等上下文暂未接入。

## 当前数据源

- 免费，不需要 token。
- 专门面向中国 A 股。
- 支持历史 K 线、成交量、成交额、换手率、是否 ST 等字段。
- 更适合当前第一版的日线级规则分析。
- 当前已接入为主数据源。

## AKShare 与东方财富风控

- 当前 `AKShare.stock_zh_a_hist()` 源码确认直接请求 `https://push2his.eastmoney.com/api/qt/stock/kline/get`，因此这个日 K 函数本身就是东方财富数据源。
- AKShare 项目 issue #7119 提到的处理思路是手动访问东方财富页面获取 cookie，并在出现验证码时人工通过验证。这说明东方财富接口存在风控/验证码场景。
- 当前第一版不自动处理验证码和 cookie。自动绕过验证码不稳定，也不适合做成本地工具的默认能力。
- 因此当前数据源顺序为：BaoStock 主源，AKShare/东方财富备用。

