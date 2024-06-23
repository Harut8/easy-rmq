import functools

from dependency_injector.wiring import Provide, inject

from pub_sub.schemas import BindingSchema, ExchangeSchema

from pub_sub.rmq_adapter import RabbitMQ, with_mq_message


class PubSubMiddleware:
    @inject
    def __init__(self, rmq_client: RabbitMQ = Provide[RabbitMQ]):
        self._rmq_client = rmq_client
        self._bindings = []

    @property
    def rmq_client(self) -> RabbitMQ:
        return self._rmq_client

    def _add_decorator(self, func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            _binding = self._bindings.pop()
            await self._rmq_client.add_binding(_binding)
            await self._rmq_client.consume_messages(_binding.queue_name, with_mq_message(func))
        return wrapper

    def subscribe(
            self,
            queue_name: str,
            route_key: str,
            exchange_name: str
    ):
        binding = BindingSchema(
            route_key=route_key,
            queue_name=queue_name,
            exchange=ExchangeSchema(
                name=exchange_name,
                type='topic',
                is_durable=True
            ),
            is_durable=True
        )

        self._bindings.append(binding)
        return self._add_decorator
