"""Browser acceptance against real local logs, using installed Chrome and CDP."""
import argparse
import base64
import json
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from websockets.sync.client import connect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True)
    parser.add_argument("--compare", required=True)
    parser.add_argument("--out", type=Path, default=Path("logs/local_20261025_data"))
    parser.add_argument("--port", type=int, default=7860)
    parser.add_argument("--debug-port", type=int, default=7861)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    url = (
        f"http://127.0.0.1:{args.port}/?"
        + urlencode(dict(run=args.run, compare=args.compare))
    )
    with tempfile.TemporaryDirectory(prefix="supermimic-browser-") as profile:
        chrome = subprocess.Popen(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu",
                  f"--user-data-dir={profile}", f"--remote-debugging-port={args.debug_port}",
                  "--window-size=1440,2600", url],
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            pages = []
            for _ in range(60):
                try:
                    pages = json.load(
                        urlopen(
                            f"http://127.0.0.1:{args.debug_port}/json/list", timeout=1
                        )
                    )
                    if any(p.get("type") == "page" for p in pages):
                        break
                except OSError:
                    pass
                time.sleep(.2)
            page = next(p for p in pages if p.get("type") == "page")
            with connect(page["webSocketDebuggerUrl"], max_size=20_000_000) as ws:
                counter, errors = 0, []
                def call(method, params=None):
                    nonlocal counter
                    counter += 1
                    ws.send(json.dumps(dict(id=counter, method=method, params=params or {})))
                    while True:
                        message = json.loads(ws.recv(timeout=15))
                        if message.get("method") == "Runtime.exceptionThrown":
                            errors.append(message["params"])
                        if message.get("id") == counter:
                            if "error" in message:
                                raise RuntimeError(message["error"])
                            return message.get("result", {})
                def evaluate(expression):
                    r = call("Runtime.evaluate", dict(expression=expression, awaitPromise=True, returnByValue=True))
                    if r.get("exceptionDetails"):
                        raise RuntimeError(r["exceptionDetails"])
                    return r.get("result", {}).get("value")
                call("Runtime.enable")
                for _ in range(60):
                    if (
                        evaluate("document.querySelectorAll('#charts .chart svg').length") == 8
                        and evaluate("document.querySelectorAll('#resource-charts .chart svg').length") == 3
                    ):
                        break
                    time.sleep(.2)
                result = evaluate("({run:document.querySelector('#run').value,compare:document.querySelector('#compare').value,charts:document.querySelectorAll('#charts .chart svg').length,resourceCharts:document.querySelectorAll('#resource-charts .chart svg').length,resourceBadge:document.querySelector('#resource-badge').textContent,resourceRows:document.querySelectorAll('#resource-compare tbody tr').length,demo:document.querySelector('#demo-content').textContent,status:document.querySelector('#status').textContent,progress:document.querySelector('#progress-label').textContent,budget:document.querySelector('#budget').textContent,config:Array.from(document.querySelectorAll('#config tbody tr')).map(r=>Array.from(r.children).map(c=>c.textContent)),checkpoint:document.querySelector('#ckpt-path').textContent,overflow:document.documentElement.scrollWidth>innerWidth})")
                diagnostic = json.dumps(
                    dict(result=result, javascript_errors=errors), ensure_ascii=False
                )
                assert result["run"] == args.run and result["compare"] == args.compare, diagnostic
                assert result["charts"] >= 7 and result["resourceCharts"] == 3, diagnostic
                assert result["resourceRows"] >= 8 and "Track B" in result["demo"], diagnostic
                assert not result["overflow"], diagnostic
                assert "训练时间上限" in result["budget"], diagnostic
                image = call("Page.captureScreenshot", dict(format="png"))["data"]
                (args.out / "dashboard_comparison.png").write_bytes(base64.b64decode(image))
                layout = call("Page.getLayoutMetrics")["cssContentSize"]
                image = call(
                    "Page.captureScreenshot",
                    dict(
                        format="png",
                        captureBeyondViewport=True,
                        clip={
                            "x": 0,
                            "y": 0,
                            "width": layout["width"],
                            "height": layout["height"],
                            "scale": 1,
                        },
                    ),
                )["data"]
                (args.out / "dashboard_full.png").write_bytes(base64.b64decode(image))
                result["full_page_css_size"] = layout
                call("Emulation.setDeviceMetricsOverride", dict(width=390, height=2200, deviceScaleFactor=1, mobile=True))
                time.sleep(.3)
                result["mobile_overflow"] = evaluate("document.documentElement.scrollWidth>innerWidth")
                assert not result["mobile_overflow"], diagnostic
                image = call("Page.captureScreenshot", dict(format="png"))["data"]
                (args.out / "dashboard_mobile_current.png").write_bytes(base64.b64decode(image))
                layout = call("Page.getLayoutMetrics")["cssContentSize"]
                image = call(
                    "Page.captureScreenshot",
                    dict(
                        format="png",
                        captureBeyondViewport=True,
                        clip={
                            "x": 0,
                            "y": 0,
                            "width": layout["width"],
                            "height": layout["height"],
                            "scale": 1,
                        },
                    ),
                )["data"]
                (args.out / "dashboard_mobile_full.png").write_bytes(base64.b64decode(image))
                result["mobile_full_page_css_size"] = layout
                result["javascript_errors"] = errors
                assert not errors, diagnostic
                (args.out / "browser_acceptance.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
                print(json.dumps(result, ensure_ascii=False, indent=2))
        finally:
            chrome.terminate()
            try:
                chrome.wait(timeout=5)
            except subprocess.TimeoutExpired:
                chrome.kill()
                chrome.wait()


if __name__ == "__main__":
    main()
