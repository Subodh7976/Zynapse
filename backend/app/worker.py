from functools import partial
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import AsyncIO

from config import REDIS_HOST, REDIS_PREFIX, redis_repo
from core.schema import ChatRequest
from services import chat


redis_broker = RedisBroker(host=REDIS_HOST, middleware=[
                           AsyncIO()], namespace=REDIS_PREFIX)
dramatiq.set_broker(redis_broker)

print(f"Redis broker initialized with host: {REDIS_HOST}")


async def async_chat(request_id: str, request: str):
    print(f"Entering async_tutor function with request_id: {request_id}")

    request: ChatRequest = ChatRequest.model_validate_json(request)
    print(f"Validated chat request: {request.model_dump_json()}")

    response_generator = chat(request.query, request.page_id, request_id, redis_repo)

    async for state in response_generator:
        print(f"Received state: {state}")
        state = state.model_dump()

        redis_repo.update_record(record_id=request_id, record=state)
        print(f"Updated Redis record for request_id: {request_id}")
    print("Finished processing tutor request")


async_chat_task = dramatiq.actor(async_chat)
