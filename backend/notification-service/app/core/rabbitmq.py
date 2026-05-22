"""
RabbitMQ consumer — dinler: exchange=job_events, queue=new_job_postings, key=job.created
Her mesajda alert_matcher çağrılır.
"""
import certifi
import json
import logging
import ssl

import aio_pika
from aio_pika.abc import AbstractRobustConnection

from .config import settings

logger = logging.getLogger(__name__)

_ssl_ctx = ssl.create_default_context(cafile=certifi.where())

EXCHANGE_NAME = "job_events"
QUEUE_NAME    = "new_job_postings"
ROUTING_KEY   = "job.created"

_connection: AbstractRobustConnection | None = None


async def connect_rabbitmq(on_message) -> None:
    """Bağlan ve mesaj dinlemeye başla. on_message(payload: dict) coroutine."""
    global _connection
    _connection = await aio_pika.connect_robust(
        settings.rabbitmq_url, ssl=True, ssl_context=_ssl_ctx
    )
    channel = await _connection.channel()
    await channel.set_qos(prefetch_count=10)

    exchange = await channel.declare_exchange(
        EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
    )
    queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    await queue.bind(exchange, routing_key=ROUTING_KEY)

    async def _handle(message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                payload = json.loads(message.body)
                await on_message(payload)
            except Exception as e:
                logger.exception("Mesaj işlenirken hata: %s", e)

    await queue.consume(_handle)
    logger.info("RabbitMQ consumer başlatıldı — queue='%s'", QUEUE_NAME)


async def disconnect_rabbitmq() -> None:
    global _connection
    if _connection and not _connection.is_closed:
        await _connection.close()
        _connection = None
        logger.info("RabbitMQ disconnected")
