"""
RabbitMQ message queue repository implementation.
"""

import asyncio
import json
import logging
from typing import Callable, Dict, Any
from urllib.parse import urlparse

import aio_pika
from aio_pika import connect_robust, Message, DeliveryMode

from app.domain.repositories import MessageQueueRepository

logger = logging.getLogger(__name__)


class RabbitMQMessageRepository(MessageQueueRepository):
    """RabbitMQ implementation of MessageQueueRepository."""
    
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.connection = None
        self.channel = None
        self._consumers: Dict[str, asyncio.Task] = {}
        
    async def connect(self) -> None:
        """Establish connection to RabbitMQ."""
        try:
            self.connection = await connect_robust(self.connection_url)
            self.channel = await self.connection.channel()
            
            # Set QoS for fair dispatch
            await self.channel.set_qos(prefetch_count=1)
            
            logger.info("Successfully connected to RabbitMQ")
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close connection to RabbitMQ."""
        try:
            # Stop all consumers
            for task in self._consumers.values():
                task.cancel()
            
            if self.channel:
                await self.channel.close()
            
            if self.connection:
                await self.connection.close()
                
            logger.info("Disconnected from RabbitMQ")
            
        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {e}")
    
    async def publish_message(self, queue: str, message: dict) -> bool:
        """Publish a message to a queue."""
        try:
            if not self.channel:
                await self.connect()
            
            # Ensure queue exists
            await self._ensure_queue_exists(queue)
            
            # Create message
            message_body = json.dumps(message).encode('utf-8')
            rabbit_message = Message(
                body=message_body,
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type='application/json'
            )
            
            # Publish message
            await self.channel.default_exchange.publish(
                rabbit_message,
                routing_key=queue
            )
            
            logger.info(f"Successfully published message to queue: {queue}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish message to queue {queue}: {e}")
            return False
    
    async def consume_messages(self, queue: str, callback: Callable) -> None:
        """Consume messages from a queue."""
        try:
            if not self.channel:
                await self.connect()
            
            # Ensure queue exists
            await self._ensure_queue_exists(queue)
            
            # Create consumer task
            consumer_task = asyncio.create_task(
                self._consume_queue(queue, callback)
            )
            
            self._consumers[queue] = consumer_task
            
            logger.info(f"Started consuming messages from queue: {queue}")
            
        except Exception as e:
            logger.error(f"Failed to start consuming from queue {queue}: {e}")
            raise
    
    async def _consume_queue(self, queue: str, callback: Callable) -> None:
        """Internal method to consume messages from a queue."""
        try:
            async with self.channel.queue_declare(queue, durable=True) as queue_obj:
                async with queue_obj.iterator() as queue_iter:
                    async for message in queue_iter:
                        async with message.process():
                            try:
                                # Parse message body
                                message_body = json.loads(message.body.decode('utf-8'))
                                
                                # Call callback
                                await callback(message_body, message.delivery.delivery_tag)
                                
                            except json.JSONDecodeError as e:
                                logger.error(f"Failed to decode message from queue {queue}: {e}")
                                await self.reject_message(message.delivery.delivery_tag, requeue=False)
                            except Exception as e:
                                logger.error(f"Error processing message from queue {queue}: {e}")
                                await self.reject_message(message.delivery.delivery_tag, requeue=True)
                                
        except Exception as e:
            logger.error(f"Error in consumer for queue {queue}: {e}")
    
    async def acknowledge_message(self, delivery_tag: int) -> bool:
        """Acknowledge a processed message."""
        try:
            if self.channel:
                await self.channel.default_exchange.publish(
                    Message(body=b'', delivery_mode=DeliveryMode.NOT_PERSISTENT),
                    routing_key=f'ack_{delivery_tag}'
                )
                logger.debug(f"Acknowledged message with delivery tag: {delivery_tag}")
                return True
        except Exception as e:
            logger.error(f"Failed to acknowledge message {delivery_tag}: {e}")
            return False
    
    async def reject_message(self, delivery_tag: int, requeue: bool = True) -> bool:
        """Reject a message."""
        try:
            if self.channel:
                await self.channel.default_exchange.publish(
                    Message(body=b'', delivery_mode=DeliveryMode.NOT_PERSISTENT),
                    routing_key=f'reject_{delivery_tag}_{requeue}'
                )
                logger.debug(f"Rejected message with delivery tag: {delivery_tag}, requeue: {requeue}")
                return True
        except Exception as e:
            logger.error(f"Failed to reject message {delivery_tag}: {e}")
            return False
    
    async def get_queue_length(self, queue: str) -> int:
        """Get the number of messages in a queue."""
        try:
            if not self.channel:
                await self.connect()
            
            # Declare queue to get its properties
            queue_obj = await self.channel.declare_queue(queue, durable=True, passive=True)
            return queue_obj.declaration_result.message_count
            
        except Exception as e:
            logger.error(f"Failed to get queue length for {queue}: {e}")
            return 0
    
    async def _ensure_queue_exists(self, queue: str) -> None:
        """Ensure a queue exists, create it if it doesn't."""
        try:
            await self.channel.declare_queue(
                queue,
                durable=True,
                auto_delete=False
            )
        except Exception as e:
            logger.error(f"Error ensuring queue {queue} exists: {e}")
    
    async def purge_queue(self, queue: str) -> bool:
        """Purge all messages from a queue."""
        try:
            if not self.channel:
                await self.connect()
            
            await self.channel.declare_queue(queue, durable=True)
            await self.channel.purge_queue(queue)
            
            logger.info(f"Purged queue: {queue}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to purge queue {queue}: {e}")
            return False
    
    async def get_queue_info(self, queue: str) -> Dict[str, Any]:
        """Get detailed information about a queue."""
        try:
            if not self.channel:
                await self.connect()
            
            queue_obj = await self.channel.declare_queue(queue, durable=True, passive=True)
            
            return {
                "name": queue,
                "message_count": queue_obj.declaration_result.message_count,
                "consumer_count": queue_obj.declaration_result.consumer_count,
                "durable": True,
                "auto_delete": False
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue info for {queue}: {e}")
            return {}
    
    async def create_exchange(self, exchange_name: str, exchange_type: str = "direct") -> bool:
        """Create a new exchange."""
        try:
            if not self.channel:
                await self.connect()
            
            await self.channel.declare_exchange(
                exchange_name,
                exchange_type,
                durable=True
            )
            
            logger.info(f"Created exchange: {exchange_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create exchange {exchange_name}: {e}")
            return False
    
    async def bind_queue_to_exchange(self, queue: str, exchange: str, routing_key: str) -> bool:
        """Bind a queue to an exchange with a routing key."""
        try:
            if not self.channel:
                await self.connect()
            
            await self.channel.declare_queue(queue, durable=True)
            await self.channel.declare_exchange(exchange, durable=True)
            
            await self.channel.bind_queue(
                queue,
                exchange,
                routing_key
            )
            
            logger.info(f"Bound queue {queue} to exchange {exchange} with routing key {routing_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to bind queue {queue} to exchange {exchange}: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check if the connection to RabbitMQ is healthy."""
        try:
            if not self.connection or self.connection.is_closed:
                return False
            
            # Try to get channel info
            if self.channel and not self.channel.is_closed:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False 