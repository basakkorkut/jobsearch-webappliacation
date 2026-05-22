"""
ReAct agent loop:
  1. Send messages + tools to LM Studio
  2. If model returns tool_calls → execute tool → append result → repeat
  3. Max 3 tool call iterations, then return final answer
"""
import json
import logging
from typing import Any

import httpx

from ..core.config import settings
from .tools import TOOL_DEFINITIONS, call_tool

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 3

SYSTEM_PROMPT = """Sen bir iş arama asistanısın. Kullanıcılara Türkiye'deki iş ilanlarını bulmalarında yardım ediyorsun.

Kullanıcı bir pozisyon veya iş hakkında sorduğunda search_jobs aracını kullan.
Belirli bir ilanın detaylarını öğrenmek istediğinde get_job_detail aracını kullan.

Yanıtlarını Türkçe ver. Kısa, net ve yardımcı ol.
İş ilanı bulamazsan alternatif anahtar kelimeler öner."""


async def _call_lm_studio(messages: list[dict]) -> dict:
    """Single call to LM Studio /v1/chat/completions."""
    payload = {
        "model": settings.lm_studio_model,
        "messages": messages,
        "tools": TOOL_DEFINITIONS,
        "tool_choice": "auto",
        "temperature": 0.7,
        "max_tokens": 1024,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{settings.lm_studio_url}/v1/chat/completions",
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()


async def run_agent(conversation: list[dict[str, Any]]) -> str:
    """
    Run the ReAct loop.
    `conversation` is the full chat history from the frontend:
      [{"role": "user"|"assistant", "content": "..."}]
    Returns the final assistant text response.
    """
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversation)

    for iteration in range(MAX_ITERATIONS):
        try:
            result = await _call_lm_studio(messages)
        except httpx.ConnectError:
            logger.error("LM Studio bağlantı hatası — %s", settings.lm_studio_url)
            return "LM Studio çevrimdışı. Lütfen uygulamayı başlatıp tekrar dene."
        except httpx.HTTPStatusError as e:
            logger.error("LM Studio HTTP hatası: %s", e)
            return "AI servisi şu an yanıt veremiyor."
        except Exception as e:
            logger.exception("LM Studio beklenmeyen hata: %s", e)
            return "Beklenmeyen bir hata oluştu."

        choice = result["choices"][0]
        message = choice["message"]
        finish_reason = choice.get("finish_reason", "")

        # No tool call → return the answer
        if finish_reason != "tool_calls" or not message.get("tool_calls"):
            return message.get("content") or "Yanıt alınamadı."

        # Execute each tool call
        # reasoning_content LM Studio'nun response-only alanı — request'e eklenince 400 verir
        clean_msg = {k: v for k, v in message.items() if k != "reasoning_content"}
        messages.append(clean_msg)

        for tc in message["tool_calls"]:
            fn_name = tc["function"]["name"]
            try:
                fn_args = json.loads(tc["function"]["arguments"])
            except json.JSONDecodeError:
                fn_args = {}

            logger.info("Tool call [iter %d]: %s(%s)", iteration + 1, fn_name, fn_args)
            tool_result = await call_tool(fn_name, fn_args)

            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": tool_result,
            })

    # Fallback: one last call without tools to force a text answer
    try:
        # Tüm mesajlardan reasoning_content temizle
        clean_messages = [
            {k: v for k, v in m.items() if k != "reasoning_content"}
            for m in messages
        ]
        payload_no_tools = {
            "model": settings.lm_studio_model,
            "messages": clean_messages,
            "temperature": 0.7,
            "max_tokens": 512,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{settings.lm_studio_url}/v1/chat/completions",
                json=payload_no_tools,
            )
            resp.raise_for_status()
            final = resp.json()
        return final["choices"][0]["message"].get("content") or "Yanıt alınamadı."
    except Exception:
        return "Maksimum adım sayısına ulaşıldı, lütfen soruyu yeniden dene."
