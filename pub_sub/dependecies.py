from dependency_injector import containers, providers
from pub_sub.pub_sub import PubSubMiddleware
from pub_sub.rmq_adapter import RabbitMQ


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    rmq_client = providers.Singleton(
        RabbitMQ,
        url=config.RABBITMQ_URL
    )

    pub_sub = providers.Factory(
        PubSubMiddleware,
        rmq_client=rmq_client
    )
