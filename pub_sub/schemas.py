import copy
import json

from aio_pika import ExchangeType, Message, DeliveryMode
from pydantic import BaseModel, field_validator


class ExchangeSchema(BaseModel):
    name: str
    type: ExchangeType = ExchangeType.TOPIC
    is_durable: bool = True
    need_bind: bool = True


class BindingSchema(BaseModel):
    route_key: str
    queue_name: str
    exchange: ExchangeSchema
    is_durable: bool = True

    def with_route_key(self, route_key: str):
        _new_binding = copy.deepcopy(self)
        _new_binding.route_key = route_key
        return _new_binding


class SendMessageSchema(BaseModel):
    routing_key: str
    message: dict
    exchange_name: str
    binding: BindingSchema = None

    @field_validator('message')
    def validate_message(cls, v):
        if not isinstance(v, dict):
            raise ValueError('Message must be a dictionary')
        return Message(
            json.dumps(v).encode(),
            delivery_mode=DeliveryMode.NOT_PERSISTENT,
        )
