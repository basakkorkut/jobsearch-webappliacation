import certifi
import json
import logging
import ssl

import aio_pika
from aio_pika import DeliveryMode, ExchangeType, Message
from aio_pika.abc import AbstractRobustConnection

from .config import settings

_ssl_ctx = ssl.create_default_context(cafile=certifi.where())

logger = logging.getLogger(__name__)

EXCHANGE_NAME = "job_events"
QUEUE_NAME = "new_job_postings"
ROUTING_KEY = "job.created"

_connection: AbstractRobustConnection | None = None
_exchange: aio_pika.abc.AbstractExchange | None = None


async def connect_rabbitmq() -> None:
    global _connection, _exchange
    _connection = await aio_pika.connect_robust(settings.rabbitmq_url, ssl=True, ssl_context=_ssl_ctx)
    channel = await _connection.channel()
    _exchange = await channel.declare_exchange(
        EXCHANGE_NAME, ExchangeType.TOPIC, durable=True
    )
    queue = await channel.declare_queue(QUEUE_NAME, durable=True)
    await queue.bind(_exchange, routing_key=ROUTING_KEY)
    logger.info("RabbitMQ connected — exchange '%s', queue '%s'", EXCHANGE_NAME, QUEUE_NAME)


async def disconnect_rabbitmq() -> None:
    global _connection
    if _connection and not _connection.is_closed:
        await _connection.close()
        _connection = None
        logger.info("RabbitMQ disconnected")


async def publish_job_created(payload: dict) -> None:
    if _exchange is None:
        logger.warning("RabbitMQ exchange not ready — skipping publish")
        return
    message = Message(
        body=json.dumps(payload, default=str).encode(),
        content_type="application/json",
        delivery_mode=DeliveryMode.PERSISTENT,
    )
    await _exchange.publish(message, routing_key=ROUTING_KEY)
    logger.info("Published job.created for job_id=%s", payload.get("job_posting_id"))
