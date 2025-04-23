from datetime import timedelta
import redis
import json
import uuid

class RedisRepository:
    def __init__(self, prefix: str, redis_host: str, merge_type: str, redis_port: int = 6379, ttl: int = 300):
        self.redis_client = redis.StrictRedis(
            host=redis_host, port=redis_port, decode_responses=True)
        self.ttl = ttl
        self.prefix = prefix
        self.merge_type = merge_type

    def _generate_key(self, record_id: str) -> str:
        return f"{self.prefix}:{record_id}"

    def create_record(self, record: dict = None) -> str:
        record_id = str(uuid.uuid4())
        if not record:
            record = {
                "type": "status",
                "content": "queued"
            }
        key = self._generate_key(record_id)
        self.redis_client.setex(key, timedelta(
            seconds=self.ttl), json.dumps(record))
        return record_id

    def update_record(self, record_id: str, record: dict) -> bool:
        key = self._generate_key(record_id)
        print("Updating record: ", record)
        if self.redis_client.exists(key):
            existing_record = json.loads(self.redis_client.get(key))

            if 'updates' not in existing_record:
                existing_record['updates'] = []

            updates = existing_record.pop("updates")

            if ("type" in record and record['type'] == self.merge_type) and \
                    ("type" in existing_record and existing_record['type'] == self.merge_type):
                pass
            else:
                # Add current state to history
                updates.append(existing_record.copy())
            record['updates'] = updates

            self.redis_client.setex(key, timedelta(
                seconds=self.ttl), json.dumps(record))

            return True
        return False

    def get_record(self, record_id: str) -> dict:
        key = self._generate_key(record_id)
        record = self.redis_client.get(key)
        if record:
            print("Fetching record: ")
            print(record)
            return json.loads(record)
        print("No record found for id - ", record_id)
        return None
