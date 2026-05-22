"""
ReAct agent loop:
  1. Send messages + tools to LM Studio
  2. If model returns tool_calls → execute tool → append result → repeat
  3. Max 3 tool call iterations, then return final answer
"""
import json
import logging
import re
from typing import Any

import httpx

from ..core.config import settings
from .tools import TOOL_DEFINITIONS, call_tool

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 3

SYSTEM_PROMPT = """Sen bir iş arama asistanısın. Kullanıcılara Türkiye'deki iş ilanlarını bulmalarında yardım ediyorsun.

ÖNEMLİ KURALLAR:
1. Kullanıcı herhangi bir iş, pozisyon, sektör veya çalışma imkanı hakkında sorduğunda MUTLAKA search_jobs aracını çağır.
2. Asla kendi bilginden iş ilanı, şirket adı veya pozisyon üretme. Sadece search_jobs aracının döndürdüğü gerçek verileri kullan.
3. İlan bulunamazsa bunu açıkça söyle ve farklı arama terimleri öner.
4. Belirli bir ilanın detaylarını öğrenmek istediğinde get_job_detail aracını kullan.

Yanıtlarını Türkçe ver. Kısa, net ve yardımcı ol."""


def _extract_content(message: dict) -> str:
    """
    QWen3 thinking modeli bazen content'i boş bırakıp reasoning_content'e yazar.
    İkisini de kontrol et; <think> bloklarını temizle.
    """
    content = message.get("content") or ""
    if not content:
        content = message.get("reasoning_content") or ""
    # <think>...</think> bloklarını kaldır
    content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL)
    return content.strip()


async def _call_lm_studio(messages: list[dict]) -> dict:
    """Single call to LM Studio /v1/chat/completions."""
    payload = {
        "model": settings.lm_studio_model,
        "messages": messages,
        "tools": TOOL_DEFINITIONS,
        "tool_choice": "auto",
        "temperature": 0.3,
        "max_tokens": 1024,
    }
    async with httpx.AsyncClient(timeout=90) as client:
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
            logger.warning("LM Studio erişilemiyor — %s", settings.lm_studio_url)
            return "LM Studio çevrimdışı. Lütfen LM Studio'yu açıp bir model yükle, sonra tekrar dene."
        except httpx.HTTPStatusError as e:
            logger.error("LM Studio HTTP hatası: %s", e)
            # tool_choice parametresi desteklenmiyorsa tekrar dene
            if e.response.status_code in (400, 422):
                return await _run_without_tool_choice(messages)
            return "AI servisi şu an yanıt veremiyor, lütfen tekrar dene."
        except Exception as e:
            logger.exception("LM Studio beklenmeyen hata: %s", e)
            return "Beklenmeyen bir hata oluştu."

        choice = result["choices"][0]
        message = choice["message"]
        finish_reason = choice.get("finish_reason", "")

        # No tool call → return the answer
        if finish_reason != "tool_calls" or not message.get("tool_calls"):
            content = _extract_content(message)
            return content or "Yanıt alınamadı."

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

            # Sonuç boşsa döngüyü erken bitir — modelin tekrar aramasını önle
            if "bulunamadı" in tool_result or "hata" in tool_result.lower():
                return _summarize_no_results(tool_result)

    # Fallback: one last call without tools to force a text answer
    # Sadece system + user mesajlarını gönder — tool mesajları LM Studio'yu patlatır
    return await _run_without_tool_choice(messages)


def _summarize_no_results(tool_result: str) -> str:
    """Tool sonucu boş geldiğinde sabit bir yanıt döndür."""
    return (
        f"{tool_result}\n\n"
        "Farklı bir arama terimi veya şehir deneyebilirsin. "
        "Örneğin pozisyon adı (\"backend developer\", \"veri analisti\") ya da büyük şehirler (İstanbul, İzmir, Ankara) ile aramayı tekrar dene."
    )


async def _run_without_tool_choice(messages: list[dict]) -> str:
    """Son çare: sadece system + user mesajlarını gönder, tool mesajları LM Studio'yu patlatır."""
    try:
        # Tool/assistant-with-tool_calls mesajlarını filtrele
        simple_messages = [
            {k: v for k, v in m.items() if k != "reasoning_content"}
            for m in messages
            if m.get("role") in ("system", "user")
        ]
        payload = {
            "model": settings.lm_studio_model,
            "messages": simple_messages,
            "temperature": 0.3,
            "max_tokens": 512,
        }
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{settings.lm_studio_url}/v1/chat/completions",
                json=payload,
            )
            resp.raise_for_status()
            final = resp.json()
        content = _extract_content(final["choices"][0]["message"])
        return content or "Yanıt alınamadı."
    except Exception:
        return "Maksimum adım sayısına ulaşıldı, lütfen soruyu yeniden dene."
