#!/usr/bin/env python3
"""Lottery assistant for 大乐透 and 双色球.

Features:
- Analyze historical draws with frequency scoring.
- Generate recommended single/复式 tickets under budget (2~10 CNY).
- Track purchases and settle against official draw results.
- Report cumulative cost, winnings and P/L.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
HISTORY_FILE = DATA_DIR / "history.json"
BETS_FILE = DATA_DIR / "bets.json"
PRIZE_FILE = DATA_DIR / "prize_rules.json"


@dataclass
class LotterySpec:
    name: str
    front_count: int
    front_min: int
    front_max: int
    back_count: int
    back_min: int
    back_max: int


SPECS: Dict[str, LotterySpec] = {
    "dlt": LotterySpec("大乐透", 5, 1, 35, 2, 1, 12),
    "ssq": LotterySpec("双色球", 6, 1, 33, 1, 1, 16),
}


def ensure_data_files() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text(json.dumps({"dlt": [], "ssq": []}, ensure_ascii=False, indent=2), encoding="utf-8")
    if not BETS_FILE.exists():
        BETS_FILE.write_text(json.dumps([], ensure_ascii=False, indent=2), encoding="utf-8")
    if not PRIZE_FILE.exists():
        default_rules = {
            "dlt": {
                "5+2": 5000000,
                "5+1": 120000,
                "5+0": 10000,
                "4+2": 3000,
                "4+1": 300,
                "3+2": 200,
                "4+0": 100,
                "3+1": 15,
                "2+2": 15,
                "3+0": 5,
                "1+2": 5,
                "0+2": 5,
            },
            "ssq": {
                "6+1": 5000000,
                "6+0": 200000,
                "5+1": 3000,
                "5+0": 200,
                "4+1": 200,
                "4+0": 10,
                "3+1": 10,
                "2+1": 5,
                "1+1": 5,
                "0+1": 5,
            },
        }
        PRIZE_FILE.write_text(json.dumps(default_rules, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_numbers(text: str) -> List[int]:
    nums = [int(x) for x in text.replace(",", " ").split() if x.strip()]
    return sorted(nums)


def validate_selection(spec: LotterySpec, front: List[int], back: List[int], allow_multiple: bool = False) -> None:
    min_front = spec.front_count if not allow_multiple else spec.front_count
    min_back = spec.back_count if not allow_multiple else spec.back_count
    if len(front) < min_front or len(back) < min_back:
        raise ValueError("号码数量不足")
    if len(set(front)) != len(front) or len(set(back)) != len(back):
        raise ValueError("号码不能重复")
    for n in front:
        if not (spec.front_min <= n <= spec.front_max):
            raise ValueError(f"前区/红球号码超范围: {n}")
    for n in back:
        if not (spec.back_min <= n <= spec.back_max):
            raise ValueError(f"后区/蓝球号码超范围: {n}")


def combination_cost(spec: LotterySpec, front: List[int], back: List[int]) -> int:
    return math.comb(len(front), spec.front_count) * math.comb(len(back), spec.back_count) * 2


def get_frequency_scores(records: List[dict], spec: LotterySpec) -> Tuple[Counter, Counter]:
    front_counter: Counter = Counter()
    back_counter: Counter = Counter()
    for r in records:
        for n in r["front"]:
            front_counter[n] += 1
        for n in r["back"]:
            back_counter[n] += 1
    return front_counter, back_counter


def recommend_numbers(lottery: str, budget: int) -> dict:
    if budget < 2 or budget > 10 or budget % 2 != 0:
        raise ValueError("预算仅支持 2~10 元，且必须是 2 的倍数")

    history = load_json(HISTORY_FILE)[lottery]
    spec = SPECS[lottery]
    front_counter, back_counter = get_frequency_scores(history, spec)

    # 如果历史为空则采用中间均匀策略
    if not history:
        front_ranked = list(range(spec.front_min, spec.front_max + 1))
        back_ranked = list(range(spec.back_min, spec.back_max + 1))
    else:
        front_ranked = [n for n, _ in front_counter.most_common()] + [
            n for n in range(spec.front_min, spec.front_max + 1) if n not in front_counter
        ]
        back_ranked = [n for n, _ in back_counter.most_common()] + [
            n for n in range(spec.back_min, spec.back_max + 1) if n not in back_counter
        ]

    # 从单注开始，尽量升级为 复式但不超过预算
    best_front = front_ranked[: spec.front_count]
    best_back = back_ranked[: spec.back_count]

    for extra_f in range(0, 4):
        for extra_b in range(0, 3):
            f = front_ranked[: spec.front_count + extra_f]
            b = back_ranked[: spec.back_count + extra_b]
            cost = combination_cost(spec, f, b)
            if cost <= budget:
                best_front, best_back = f, b

    return {
        "lottery": spec.name,
        "front": best_front,
        "back": best_back,
        "cost": combination_cost(spec, best_front, best_back),
        "note": "基于历史频次的启发式推荐，不保证中奖。",
    }


def add_draw(lottery: str, period: str, front: List[int], back: List[int]) -> None:
    spec = SPECS[lottery]
    validate_selection(spec, front, back, allow_multiple=False)
    if len(front) != spec.front_count or len(back) != spec.back_count:
        raise ValueError("开奖期号码必须为标准单注长度")

    history = load_json(HISTORY_FILE)
    records = history[lottery]
    if any(r["period"] == period for r in records):
        raise ValueError(f"期号已存在: {period}")

    records.append({"period": period, "front": front, "back": back, "timestamp": datetime.utcnow().isoformat()})
    records.sort(key=lambda x: x["period"])
    save_json(HISTORY_FILE, history)


def calculate_hit(lottery: str, bet_front: List[int], bet_back: List[int], draw_front: List[int], draw_back: List[int]) -> str:
    front_hit = len(set(bet_front) & set(draw_front))
    back_hit = len(set(bet_back) & set(draw_back))
    return f"{front_hit}+{back_hit}"


def settle_bets_for_period(lottery: str, period: str) -> int:
    history = load_json(HISTORY_FILE)
    bets = load_json(BETS_FILE)
    rules = load_json(PRIZE_FILE)[lottery]

    draw = next((r for r in history[lottery] if r["period"] == period), None)
    if not draw:
        raise ValueError(f"未找到开奖期号: {period}")

    changed = 0
    for bet in bets:
        if bet["lottery"] != lottery or bet.get("status") == "settled" or bet["period"] != period:
            continue
        hit_key = calculate_hit(lottery, bet["front"], bet["back"], draw["front"], draw["back"])
        win = rules.get(hit_key, 0)
        bet["hit"] = hit_key
        bet["win"] = win
        bet["status"] = "settled"
        changed += 1

    save_json(BETS_FILE, bets)
    return changed


def place_bet(lottery: str, period: str, front: List[int], back: List[int]) -> dict:
    spec = SPECS[lottery]
    validate_selection(spec, front, back, allow_multiple=True)
    cost = combination_cost(spec, front, back)
    if cost < 2 or cost > 10:
        raise ValueError("仅支持 2~10 元投注")

    bets = load_json(BETS_FILE)
    entry = {
        "id": len(bets) + 1,
        "lottery": lottery,
        "period": period,
        "front": front,
        "back": back,
        "cost": cost,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat(),
    }
    bets.append(entry)
    save_json(BETS_FILE, bets)
    return entry


def profit_report(lottery: str | None = None) -> dict:
    bets = load_json(BETS_FILE)
    selected = [b for b in bets if lottery is None or b["lottery"] == lottery]
    total_cost = sum(b["cost"] for b in selected)
    total_win = sum(b.get("win", 0) for b in selected)
    pending = sum(1 for b in selected if b.get("status") != "settled")
    return {
        "bets": len(selected),
        "pending": pending,
        "total_cost": total_cost,
        "total_win": total_win,
        "profit": total_win - total_cost,
    }


def cmd_recommend(args):
    rec = recommend_numbers(args.lottery, args.budget)
    print(json.dumps(rec, ensure_ascii=False, indent=2))


def cmd_add_draw(args):
    add_draw(args.lottery, args.period, parse_numbers(args.front), parse_numbers(args.back))
    settled = settle_bets_for_period(args.lottery, args.period)
    print(f"已录入开奖 {args.lottery} {args.period}，自动结算 {settled} 笔投注")


def cmd_place_bet(args):
    bet = place_bet(args.lottery, args.period, parse_numbers(args.front), parse_numbers(args.back))
    print("投注成功:")
    print(json.dumps(bet, ensure_ascii=False, indent=2))


def cmd_settle(args):
    settled = settle_bets_for_period(args.lottery, args.period)
    print(f"已结算 {settled} 笔")


def cmd_report(args):
    rpt = profit_report(args.lottery)
    print(json.dumps(rpt, ensure_ascii=False, indent=2))


def build_parser():
    parser = argparse.ArgumentParser(description="大乐透/双色球 彩票助手")
    sub = parser.add_subparsers(required=True)

    p1 = sub.add_parser("recommend", help="推荐号码")
    p1.add_argument("lottery", choices=SPECS.keys())
    p1.add_argument("budget", type=int, help="预算(2-10, 偶数)")
    p1.set_defaults(func=cmd_recommend)

    p2 = sub.add_parser("add-draw", help="录入开奖号码")
    p2.add_argument("lottery", choices=SPECS.keys())
    p2.add_argument("period", help="期号")
    p2.add_argument("--front", required=True, help="前区/红球号码，空格或逗号分隔")
    p2.add_argument("--back", required=True, help="后区/蓝球号码，空格或逗号分隔")
    p2.set_defaults(func=cmd_add_draw)

    p3 = sub.add_parser("place-bet", help="记录投注")
    p3.add_argument("lottery", choices=SPECS.keys())
    p3.add_argument("period", help="投注期号")
    p3.add_argument("--front", required=True)
    p3.add_argument("--back", required=True)
    p3.set_defaults(func=cmd_place_bet)

    p4 = sub.add_parser("settle", help="手动结算期号")
    p4.add_argument("lottery", choices=SPECS.keys())
    p4.add_argument("period")
    p4.set_defaults(func=cmd_settle)

    p5 = sub.add_parser("report", help="盈亏报表")
    p5.add_argument("--lottery", choices=SPECS.keys())
    p5.set_defaults(func=cmd_report)

    return parser


def main():
    ensure_data_files()
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
