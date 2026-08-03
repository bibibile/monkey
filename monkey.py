# -*- coding: utf-8 -*-

import os
import requests
from datetime import datetime, timedelta

BASE = "https://dash.monkey-network.xyz"

TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

API_KEY = os.getenv("MONKEY_API_KEY")


# =========================================================
# Telegram
# =========================================================
def send_tg(text):
    if not TG_TOKEN or not TG_CHAT_ID:
        print("⚠️ 未配置 TG")
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT_ID, "text": text}
        )
    except Exception as e:
        print("❌ TG 发送失败:", e)


# =========================================================
# Monkey API（续期 + 开机）
# =========================================================
def monkey_api_task():
    if not API_KEY:
        return "❌ 未设置 API KEY"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json"
    }

    msg = "🖥️ 服务器状态\n\n"

    try:
        res = requests.get(f"{BASE}/api/client", headers=headers).json()
    except Exception as e:
        return f"❌ API 请求失败: {e}"

    for s in res.get("data", []):
        name = s["attributes"]["name"]
        uuid = s["attributes"]["uuid"]

        # 生命周期
        try:
            life = requests.get(
                f"{BASE}/api/client/servers/{uuid}/lifecycle",
                headers=headers
            ).json()
        except:
            life = {}

        days = life.get("days_remaining", 0)
        confirm = life.get("can_confirm", False)

        # 状态
        try:
            res2 = requests.get(
                f"{BASE}/api/client/servers/{uuid}/resources",
                headers=headers
            ).json()
        except:
            res2 = {}

        state = res2.get("attributes", {}).get("current_state", "unknown")

        # 自动续期
        if days <= 7 and confirm:
            try:
                requests.post(
                    f"{BASE}/api/client/servers/{uuid}/lifecycle/confirm",
                    headers=headers
                )
                confirm_text = "♻️已续期"
            except:
                confirm_text = "❌续期失败"
        else:
            confirm_text = "✔️正常"

        # 自动开机
        if state == "offline":
            try:
                requests.post(
                    f"{BASE}/api/client/servers/{uuid}/power",
                    headers={**headers, "Content-Type": "application/json"},
                    json={"signal": "start"}
                )
                state_text = "🚀已启动"
            except:
                state_text = "❌启动失败"
        else:
            state_text = f"✔️{state}"

        line = f"{name} | {days}天 | {confirm_text} | {state_text}"
        print(line)
        msg += line + "\n"

    return msg


# =========================================================
# MAIN
# =========================================================
def main():
    print("🚀 开始执行 Monkey API 任务")

    api_report = monkey_api_task()

    bj_time = datetime.utcnow() + timedelta(hours=8)

    final_msg = (
        api_report
        + "\n⏱ "
        + bj_time.strftime('%Y-%m-%d %H:%M:%S')
    )

    print("\n📩 发送 TG 通知")
    send_tg(final_msg)


if __name__ == "__main__":
    main()