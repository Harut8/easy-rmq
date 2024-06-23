import json
import logging
import sys

from aio_pika import IncomingMessage, connect
from aio_pika.abc import AbstractQueue, AbstractExchange, AbstractChannel, AbstractConnection
from pydantic import AmqpDsn

from pub_sub.schemas import BindingSchema, SendMessageSchema

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
_logger.addHandler(logging.StreamHandler(sys.stdout))


class RabbitMQ:
    logger = _logger

    def __init__(
            self,
            url: AmqpDsn,
    ):
        self._url = url
        self._connection: AbstractConnection | None = None
        self._channel: AbstractChannel | None = None
        self._exchanges: dict[str, AbstractExchange] = {}
        self._bindings: list[BindingSchema] = []
        self._processed_bindings: list[BindingSchema] = []
        self._queues: list[AbstractQueue] = []

    @property
    def connection(self) -> AbstractConnection:
        return self._connection

    @property
    def channel(self) -> AbstractChannel:
        return self._channel

    @property
    def exchanges(self) -> dict[str, AbstractExchange]:
        return self._exchanges

    @property
    def bindings(self) -> list[BindingSchema]:
        return self._bindings

    async def connect(self):
        self._connection = await connect(self._url)
        self._channel = await self._connection.channel()
        RabbitMQ.logger.info("Connected to RabbitMQ")

    async def add_binding(self, binding: BindingSchema):
        self._bindings.append(binding)

    async def declare_queue(self, queue_name):
        for _binding in self._bindings:
            if _binding.queue_name == queue_name:
                _queue: AbstractQueue = await self.channel.declare_queue(
                    name=_binding.queue_name,
                    durable=_binding.is_durable
                )
                if _binding.exchange.name not in self._exchanges:
                    self._exchanges[_binding.exchange.name] = await self.channel.declare_exchange(
                        name=_binding.exchange.name,
                        type=_binding.exchange.type,
                        durable=_binding.exchange.is_durable
                    )
                    self.logger.info(f"Declared exchange: {_binding.exchange.name}")
                if _binding.exchange.need_bind:
                    await _queue.bind(
                        exchange=self._exchanges[_binding.exchange.name],
                        routing_key=_binding.route_key
                    )
                    self.bindings.remove(_binding)
                    self.logger.info(f"Bound queue: {queue_name}"
                                     f" to exchange: {_binding.exchange.name}"
                                     f" with routing key: {_binding.route_key}")

                return _queue

    async def send_message(
            self,
            message_schema: SendMessageSchema

    ):
        if message_schema.binding:
            await self.declare_queue(message_schema.binding.queue_name)
        await self.exchanges[message_schema.exchange_name].publish(
            message_schema.message,  # type: ignore
            message_schema.routing_key
        )
        self.logger.info(f"Sent message: {message_schema.message}"
                         f" to exchange: {message_schema.exchange_name}"
                         f" with routing key: {message_schema.routing_key}")

    async def consume_messages(self, queue_name, callback):
        if not self.connection:
            await self.connect()
        queue = await self.declare_queue(queue_name)
        await queue.consume(callback)
        RabbitMQ.logger.info(f"Consuming messages from queue: {queue_name}")


def with_mq_message(func):
    async def wrapper(_message: IncomingMessage, *args, **kwargs):
        async with _message.process():
            _payload = _message.body.decode()
            try:
                RabbitMQ.logger.info(f"Routing key: {_message.routing_key}")
                RabbitMQ.logger.info(f"Received message: \n\n\t {_payload}")
                payload = json.loads(_payload)
                await func(
                    message=payload,
                    *args,
                    **kwargs
                )
            except Exception as e:
                RabbitMQ.logger.exception(e)

    return wrapper
