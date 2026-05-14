"""
bot/feishu_server.py — 飞书事件回调服务

接收飞书消息事件 → KnowledgeBot 处理 → 通过飞书 API 回复。

启动方式：
    python -m bot.feishu_server

需要环境变量：
    FEISHU_APP_ID          飞书应用 App ID
    FEISHU_APP_SECRET      飞书应用 App Secret
    FEISHU_VERIFICATION_TOKEN  事件订阅验证令牌（开放平台配置页获取）
"""

import hashlib
import json
import logging
import os
import time
from typing import Any

import aiohttp
from aiohttp import web

from bot.knowledge_bot import KnowledgeBot

logger = logging.getLogger(__name__)

# ============================================================
# 飞书 Token 管理（带缓存）
# ============================================================

class FeishuTokenManager:
    """管理 tenant_access_token，自动缓存和刷新。"""

    TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self._token: str = ""
        self._expires_at: float = 0  # unix timestamp

    async def get_token(self) -> str:
        """获取有效的 tenant_access_token，过期前自动刷新。"""
        # 提前 5 分钟刷新，避免边界情况
        if self._token and time.time() < self._expires_at - 300:
            return self._token

        payload = {"app_id": self.app_id, "app_secret": self.app_secret}
        async with aiohttp.ClientSession() as session:
            async with session.post(self.TOKEN_URL, json=payload) as resp:
                data = await resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"获取 tenant_access_token 失败: {data}")

        self._token = data["tenant_access_token"]
        self._expires_at = time.time() + data.get("expire", 7200)
        logger.info(f"[飞书] token 已刷新，有效期 {data.get('expire', 7200)}s")
        return self._token


# ============================================================
# 飞书消息发送
# ============================================================

class FeishuMessageSender:
    """通过飞书 API 发送消息。"""

    REPLY_URL = "https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"
    SEND_URL = "https://open.feishu.cn/open-apis/im/v1/messages"

    def __init__(self, token_manager: FeishuTokenManager):
        self.token_manager = token_manager

    async def reply(self, message_id: str, text: str) -> dict:
        """回复指定消息。"""
        token = await self.token_manager.get_token()
        url = self.REPLY_URL.format(message_id=message_id)
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        payload = {
            "content": json.dumps({"text": text}),
            "msg_type": "text",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                data = await resp.json()
                if data.get("code") != 0:
                    logger.error(f"[飞书] 回复失败: {data}")
                return data

    async def send(self, chat_id: str, text: str) -> dict:
        """主动发送消息到群/用户。"""
        token = await self.token_manager.get_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        }
        payload = {
            "receive_id": chat_id,
            "content": json.dumps({"text": text}),
            "msg_type": "text",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.SEND_URL,
                headers=headers,
                json=payload,
                params={"receive_id_type": "chat_id"},
            ) as resp:
                data = await resp.json()
                if data.get("code") != 0:
                    logger.error(f"[飞书] 发送失败: {data}")
                return data


# ============================================================
# 事件处理
# ============================================================

class FeishuEventHandler:
    """处理飞书事件订阅回调。"""

    def __init__(
        self,
        verification_token: str,
        bot: KnowledgeBot,
        sender: FeishuMessageSender,
    ):
        self.verification_token = verification_token
        self.bot = bot
        self.sender = sender
        # 去重：记录最近处理过的 event_id
        self._seen_events: dict[str, float] = {}

    def _clean_seen_events(self):
        """清理 5 分钟前的 event_id 记录。"""
        cutoff = time.time() - 300
        self._seen_events = {
            eid: ts for eid, ts in self._seen_events.items() if ts > cutoff
        }

    async def handle(self, request: web.Request) -> web.Response:
        """aiohttp 路由处理函数。"""
        try:
            body = await request.json()
        except json.JSONDecodeError:
            return web.json_response({"error": "invalid json"}, status=400)

        # --- 1. URL 验证挑战（首次配置回调地址时飞书会发送） ---
        if body.get("type") == "url_verification":
            challenge = body.get("challenge", "")
            logger.info("[飞书] URL 验证挑战")
            return web.json_response({"challenge": challenge})

        # --- 2. v2.0 事件格式 ---
        header = body.get("header", {})
        event = body.get("event", {})

        # 验证 token
        if header.get("token") != self.verification_token:
            logger.warning("[飞书] verification_token 不匹配，拒绝请求")
            return web.json_response({"error": "invalid token"}, status=403)

        # 去重
        event_id = header.get("event_id", "")
        if event_id in self._seen_events:
            return web.json_response({"msg": "duplicate event"})
        self._seen_events[event_id] = time.time()
        self._clean_seen_events()

        # 只处理消息接收事件
        event_type = header.get("event_type", "")
        if event_type != "im.message.receive_v1":
            return web.json_response({"msg": "ignored"})

        # --- 3. 提取消息内容 ---
        message = event.get("message", {})
        msg_type = message.get("message_type", "")
        message_id = message.get("message_id", "")

        # 只处理文本消息
        if msg_type != "text":
            await self.sender.reply(message_id, "目前只支持文本消息哦~")
            return web.json_response({"msg": "ok"})

        # 解析消息内容
        try:
            content = json.loads(message.get("content", "{}"))
            text = content.get("text", "").strip()
        except json.JSONDecodeError:
            text = ""

        if not text:
            return web.json_response({"msg": "empty"})

        # 去掉 @机器人 的 mention 部分
        mentions = event.get("message", {}).get("mentions", [])
        for mention in mentions:
            at_key = mention.get("key", "")
            if at_key:
                text = text.replace(at_key, "").strip()

        if not text:
            await self.sender.reply(message_id, format_help_short())
            return web.json_response({"msg": "ok"})

        # --- 4. 交给 KnowledgeBot 处理 ---
        sender_id = event.get("sender", {}).get("sender_id", {}).get("open_id", "unknown")
        logger.info(f"[飞书] 收到消息: user={sender_id} text={text!r}")

        response = self.bot.handle_message(user_id=sender_id, text=text)
        await self.sender.reply(message_id, response)

        return web.json_response({"msg": "ok"})


def format_help_short() -> str:
    return "你好！我是 AI 知识库助手。试试发送「今日简报」或「搜索 MCP」"


# ============================================================
# 应用启动
# ============================================================

def create_app() -> web.Application:
    """创建 aiohttp 应用。"""
    from dotenv import load_dotenv
    load_dotenv()

    app_id = os.environ.get("FEISHU_APP_ID", "")
    app_secret = os.environ.get("FEISHU_APP_SECRET", "")
    verification_token = os.environ.get("FEISHU_VERIFICATION_TOKEN", "")

    if not all([app_id, app_secret, verification_token]):
        raise RuntimeError(
            "请设置环境变量: FEISHU_APP_ID, FEISHU_APP_SECRET, FEISHU_VERIFICATION_TOKEN"
        )

    token_manager = FeishuTokenManager(app_id, app_secret)
    sender = FeishuMessageSender(token_manager)
    bot = KnowledgeBot()
    handler = FeishuEventHandler(verification_token, bot, sender)

    app = web.Application()
    app.router.add_post("/feishu/event", handler.handle)
    # 健康检查
    app.router.add_get("/health", lambda _: web.json_response({"status": "ok"}))

    return app


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    port = int(os.environ.get("FEISHU_BOT_PORT", "9000"))
    app = create_app()
    logger.info(f"飞书事件回调服务启动，端口 {port}")
    logger.info(f"回调地址: http://<your-host>:{port}/feishu/event")
    web.run_app(app, port=port)
