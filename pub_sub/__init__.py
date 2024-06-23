from pub_sub.dependecies import Container

container = Container()
container.wire(modules=[__name__, "pub_sub"])
container.config.RABBITMQ_URL.from_env("RABBITMQ_URL")

PubSub = container.pub_sub.provided()

__all__ = ["PubSub"]
