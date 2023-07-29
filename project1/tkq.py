from taskiq_aio_pika import AioPikaBroker
import os
import taskiq_fastapi
from taskiq.receiver import Receiver
MQ_DSN = os.environ.get("MQ_DSN")

broker = AioPikaBroker(MQ_DSN)
taskiq_fastapi.init(broker, "project1.app:app")