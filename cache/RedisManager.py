import redis
import os

class RedisManager:
    def __init__(self, host=None, port=6379, db=0):
        """
        Initializes the RedisManager, connecting to a Redis instance.
        It first attempts to connect using a Redis URL from environment variables,
        then falls back to the provided host, port, and db.
        """
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            self.redis_client = redis.from_url(redis_url)
        else:
            host = host or os.getenv("REDIS_HOST", "localhost")
            self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        
        print("RedisManager initialized and connected to Redis.")

    def add_to_stream(self, stream_name: str, message: dict):
        """
        Adds a message to a Redis Stream.

        Args:
            stream_name: The name of the stream to add the message to.
            message: A dictionary representing the message to add.
        """
        try:
            self.redis_client.xadd(stream_name, message)
        except Exception as e:
            print(f"Error adding to stream {stream_name}: {e}")

    def create_consumer_group(self, stream_name: str, group_name: str):
        """
        Creates a new consumer group for a stream.
        This is idempotent; it doesn't fail if the group already exists.
        """
        try:
            self.redis_client.xgroup_create(stream_name, group_name, id='0', mkstream=True)
            print(f"Consumer group '{group_name}' created for stream '{stream_name}'.")
        except redis.exceptions.ResponseError as e:
            if "BUSYGROUP" in str(e):
                print(f"Consumer group '{group_name}' already exists for stream '{stream_name}'.")
            else:
                raise

    def read_from_stream(self, stream_name: str, group_name: str, consumer_name: str, count: int = 1):
        """
        Reads messages from a stream using a consumer group.

        Args:
            stream_name: The name of the stream to read from.
            group_name: The name of the consumer group.
            consumer_name: A unique identifier for the consumer reading the messages.
            count: The maximum number of messages to read.

        Returns:
            A list of messages or None if no new messages are available.
        """
        try:
            # ">" means read new messages that have not been delivered to any other consumer.
            response = self.redis_client.xreadgroup(group_name, consumer_name, {stream_name: '>'}, count=count)
            if response:
                # The response is structured as [[stream_name, [(message_id, message_data)]]]
                return response[0][1]
            return None
        except Exception as e:
            print(f"Error reading from stream {stream_name}: {e}")
            return None
    
    def acknowledge_message(self, stream_name: str, group_name: str, message_id: str):
        """
        Acknowledges that a message has been processed.

        Args:
            stream_name: The name of the stream.
            group_name: The name of the consumer group.
            message_id: The ID of the message to acknowledge.
        """
        try:
            self.redis_client.xack(stream_name, group_name, message_id)
        except Exception as e:
            print(f"Error acknowledging message {message_id} in stream {stream_name}: {e}") 