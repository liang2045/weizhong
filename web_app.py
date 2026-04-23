#!/usr/bin/env python3
"""No-dependency web UI for lottery assistant (stdlib HTTP server)."""

from __future__ import annotations

import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs

from lottery_assistant import (
    SPECS,
    add_draw,
    ensure_data_files,
    parse_numbers,
    place_bet,
    profit_report,
    recommend_numbers,
    settle_bets_for_period,
)

HOST = "0.0.0.0"
PORT = 8000
LAST_RECOMMENDATION: dict | None = None


def _options_html() -> str:
    return "".join(f'<option value="{k}">{v.name} ({k})</option>' for k, v in SPECS.items())


def _render_page(message: str = "", error: str = "") -> str:
    report = profit_report()
    rec_html = ""
    if LAST_RECOMMENDATION:
        rec_html = f"""
        <p><b>{html.escape(str(LAST_RECOMMENDATION['lottery']))}</b> 推荐：</p>
        <p class='mono'>前区/红球: {html.escape(str(LAST_RECOMMENDATION['front']))}</p>
        <p class='mono'>后区/蓝球: {html.escape(str(LAST_RECOMMENDATION['back']))}</p>
        <p>金额: {LAST_RECOMMENDATION['cost']} 元</p>
        <small>{html.escape(str(LAST_RECOMMENDATION['note']))}</small>
        """

    return f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<title>彩票助手</title>
<style>
body {{ font-family: Arial, sans-serif; margin:24px; background:#f6f8fb; color:#222; }}
.card {{ background:#fff; border-radius:10px; padding:14px; margin-bottom:12px; box-shadow:0 1px 6px rgba(0,0,0,.08); }}
.row {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
input,select,button {{ width:100%; padding:8px; margin-top:4px; box-sizing:border-box; }}
button {{ background:#2563eb; color:#fff; border:0; border-radius:6px; cursor:pointer; }}
.msg {{ padding:8px; border-radius:6px; margin-bottom:10px; }}
.ok {{ background:#e8f7ed; color:#137333; }} .err {{ background:#fdecec; color:#b3261e; }}
.mono {{ font-family: ui-monospace, Menlo, Consolas, monospace; }}
</style></head><body>
<h1>彩票助手（无依赖 Web 版）</h1>
{f"<div class='msg ok'>{html.escape(message)}</div>" if message else ''}
{f"<div class='msg err'>{html.escape(error)}</div>" if error else ''}
<div class='card'>
  <h3>号码推荐（2~10元）</h3>
  <form method='post' action='/recommend'>
    <div class='row'><div><label>彩种</label><select name='lottery'>{_options_html()}</select></div>
    <div><label>预算</label><select name='budget'><option>2</option><option>4</option><option>6</option><option>8</option><option>10</option></select></div></div>
    <button type='submit'>生成推荐</button>
  </form>
  {rec_html}
</div>
<div class='card'>
  <h3>记录投注</h3>
  <form method='post' action='/bet'>
    <div class='row'><div><label>彩种</label><select name='lottery'>{_options_html()}</select></div>
    <div><label>期号</label><input name='period' placeholder='如 2026045' required /></div></div>
    <label>前区/红球</label><input name='front' placeholder='01 03 08 18 23' required />
    <label>后区/蓝球</label><input name='back' placeholder='03 09' required />
    <button type='submit'>提交投注</button>
  </form>
</div>
<div class='card'>
  <h3>录入开奖号码（自动结算）</h3>
  <form method='post' action='/draw'>
    <div class='row'><div><label>彩种</label><select name='lottery'>{_options_html()}</select></div>
    <div><label>期号</label><input name='period' placeholder='如 2026045' required /></div></div>
    <label>前区/红球</label><input name='front' placeholder='01 03 08 19 23' required />
    <label>后区/蓝球</label><input name='back' placeholder='03 09' required />
    <button type='submit'>录入并结算</button>
  </form>
</div>
<div class='card'>
  <h3>盈亏概览</h3>
  <p class='mono'>总投注: {report['bets']} 笔</p>
  <p class='mono'>待结算: {report['pending']} 笔</p>
  <p class='mono'>总投入: {report['total_cost']} 元</p>
  <p class='mono'>总中奖: {report['total_win']} 元</p>
  <p class='mono'>累计盈亏: {report['profit']} 元</p>
</div>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send_html(self, content: str, status: int = 200) -> None:
        data = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):  # noqa: N802
        if self.path != "/":
            self._send_html("<h3>404 Not Found</h3>", status=404)
            return
        self._send_html(_render_page())

    def do_POST(self):  # noqa: N802
        global LAST_RECOMMENDATION
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        form = {k: v[0] for k, v in parse_qs(raw).items()}

        try:
            if self.path == "/recommend":
                LAST_RECOMMENDATION = recommend_numbers(form["lottery"], int(form["budget"]))
                self._send_html(_render_page(message="推荐生成成功"))
                return

            if self.path == "/bet":
                bet_data = place_bet(
                    form["lottery"],
                    form["period"],
                    parse_numbers(form["front"]),
                    parse_numbers(form["back"]),
                )
                self._send_html(_render_page(message=f"投注成功，金额 {bet_data['cost']} 元"))
                return

            if self.path == "/draw":
                add_draw(
                    form["lottery"],
                    form["period"],
                    parse_numbers(form["front"]),
                    parse_numbers(form["back"]),
                )
                settled = settle_bets_for_period(form["lottery"], form["period"])
                self._send_html(_render_page(message=f"开奖已录入，自动结算 {settled} 笔"))
                return

            self._send_html(_render_page(error="未知操作"), status=400)
        except Exception as exc:
            self._send_html(_render_page(error=f"操作失败: {exc}"), status=400)


def main() -> None:
    ensure_data_files()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Lottery assistant web started at http://127.0.0.1:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
