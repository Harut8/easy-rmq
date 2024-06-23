# RMQ-ROUTER

Rmq-router is python lib for easy integration rabbit consumer with fastapi

## Installation

```bash
poetry add easy-rmq
```

## Usage
Make sure in .env you declare `RABBITMQ_URL`=amqp://...

```python
from pub_sub import PubSub

@PubSub.subscribe(queue_name="hello", route_key="hello", exchange_name="hello")
async def hello(message):
    print("Welcome", message)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await hello()
    yield

app = FastAPI(lifespan=lifespan)

```
