# 彩票助手（大乐透 / 双色球）

一个轻量命令行彩票助手，支持：

- 基于历史开奖频次做号码推荐（单注到 10 元以内复式）；
- 记录每期投注；
- 录入开奖号码后自动结算；
- 统计累计投入、中奖与盈亏。

> 提醒：彩票结果是随机事件，任何“高概率号码”都无法保证中奖。本工具只提供统计辅助。

## 给不会编程的用户（最简单）

### Windows（推荐）
1. 双击 `start_app.bat`
2. 浏览器会自动打开彩票助手页面
3. 如果没自动打开，手动输入：`http://127.0.0.1:8000`

### macOS / Linux（推荐）
1. 双击（或终端运行）`start_app.sh`
2. 浏览器会自动打开彩票助手页面
3. 如果没自动打开，手动输入：`http://127.0.0.1:8000`

## 应用界面（Web）

你可以直接启动浏览器界面：

```bash
python3 web_app.py
```

启动后访问：`http://127.0.0.1:8000`

该版本不需要 Flask，开箱即用。

页面内可完成：
- 号码推荐（2~10 元）
- 投注录入
- 开奖录入并自动结算
- 实时盈亏概览

## 快速开始

```bash
python3 lottery_assistant.py recommend dlt 10
python3 lottery_assistant.py place-bet dlt 2026045 --front "01 03 08 18 23" --back "03 09"
python3 lottery_assistant.py add-draw dlt 2026045 --front "01 03 08 19 23" --back "03 09"
python3 lottery_assistant.py report
```

## 命令说明

### 1) 推荐号码

```bash
python3 lottery_assistant.py recommend <dlt|ssq> <budget>
```

- `budget`: 2~10 元，且必须是偶数。

### 2) 记录投注

```bash
python3 lottery_assistant.py place-bet <dlt|ssq> <period> --front "..." --back "..."
```

- 支持单注和复式；
- 自动计算组合注数并换算金额（2 元/注）；
- 当前限制单次投入 2~10 元。

### 3) 录入开奖结果（自动结算）

```bash
python3 lottery_assistant.py add-draw <dlt|ssq> <period> --front "..." --back "..."
```

- 录入后会自动结算该期待结算投注。

### 4) 手动结算

```bash
python3 lottery_assistant.py settle <dlt|ssq> <period>
```

### 5) 盈亏报表

```bash
python3 lottery_assistant.py report [--lottery dlt|ssq]
```

## 数据文件

- `data/history.json`: 开奖历史；
- `data/bets.json`: 投注记录；
- `data/prize_rules.json`: 奖级规则（默认内置示例金额，可自行按当期规则修改）。

## 奖金规则说明

双色球/大乐透头奖和部分奖级在现实中可能浮动。默认规则是便于离线计算盈亏的估算模板。若要更精确，请每期按官方规则更新 `data/prize_rules.json`。
