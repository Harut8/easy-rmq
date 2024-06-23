from contextlib import asynccontextmanager

from fastapi import FastAPI

from pub_sub.__init__ import PubSub


@PubSub.subscribe(queue_name='hello1', route_key='hello1', exchange_name='hello')
async def handler(message):
    print("First handler")
    print(f"Received message: {message}")


@PubSub.subscribe(queue_name='hello2', route_key='hello2', exchange_name='hello')
async def handler2(message):
    print("Second handler")
    print(f"Received message: {message}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await handler()
    await handler2()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Hello World"}


from uvicorn import run

run(app, host="0.0.0.0", port=8000)
