"""
Message Queue (MQ) service for handling payment messages.

Author: Eon (Himanshu Shekhar)
Email: himanshu.shekhar@example.com
GitHub: https://github.com/eon-himanshu
Created: 2024
"""
import logging
import json
import asyncio
from typing import Optional, Callable, Dict, Any
from datetime import datetime
import aio_pika
from aio_pika import connect_robust, Message, DeliveryMode
from app.models.schemas import PaymentMessage, MQMessage
from app.core.config import settings

logger = logging.getLogger(__name__)


class MQService:
    """Message Queue service for handling payment messages."""
    
    def __init__(self):
        """Initialize the MQ service."""
        self.connection = None
        self.channel = None
        self.exchange = None
        self.queues: Dict[str, aio_pika.Queue] = {}
        self.consumers: Dict[str, asyncio.Task] = {}
        self.message_handlers: Dict[str, Callable] = {}
        
    async def connect(self) -> None:
        """Connect to the message queue broker."""
        try:
            # Connect to RabbitMQ
            self.connection = await connect_robust(
                host=settings.mq_host,
                port=settings.mq_port,
                login=settings.mq_username,
                password=settings.mq_password,
                virtualhost=settings.mq_virtual_host
            )
            
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                settings.mq_exchange_name,
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            logger.info("Successfully connected to MQ broker")
            
        except Exception as e:
            logger.error(f"Failed to connect to MQ broker: {str(e)}")
            raise
    
    async def declare_queue(self, queue_name: str, routing_key: str = "#") -> None:
        """Declare a queue and bind it to the exchange."""
        try:
            queue = await self.channel.declare_queue(
                queue_name,
                durable=True,
                arguments={
                    "x-message-ttl": settings.mq_message_ttl,
                    "x-max-length": settings.mq_max_queue_length
                }
            )
            
            await queue.bind(self.exchange, routing_key)
            self.queues[queue_name] = queue
            
            logger.info(f"Declared queue: {queue_name} with routing key: {routing_key}")
            
        except Exception as e:
            logger.error(f"Failed to declare queue {queue_name}: {str(e)}")
            raise
    
    async def publish_message(
        self, 
        message: PaymentMessage, 
        routing_key: str,
        priority: int = 0
    ) -> None:
        """Publish a payment message to the exchange."""
        try:
            message_body = message.model_dump_json()
            
            mq_message = Message(
                body=message_body.encode(),
                delivery_mode=DeliveryMode.PERSISTENT,
                priority=priority,
                timestamp=datetime.utcnow(),
                headers={
                    "content_type": "application/json",
                    "message_type": "payment_screening"
                }
            )
            
            await self.exchange.publish(mq_message, routing_key=routing_key)
            
            logger.info(f"Published message to routing key: {routing_key}")
            
        except Exception as e:
            logger.error(f"Failed to publish message: {str(e)}")
            raise
    
    async def start_consumer(
        self, 
        queue_name: str, 
        handler: Callable[[PaymentMessage], None],
        prefetch_count: int = 10
    ) -> None:
        """Start consuming messages from a queue."""
        try:
            if queue_name not in self.queues:
                await self.declare_queue(queue_name)
            
            queue = self.queues[queue_name]
            
            # Set QoS
            await self.channel.set_qos(prefetch_count=prefetch_count)
            
            # Start consuming
            consumer_task = asyncio.create_task(
                self._consume_messages(queue, handler)
            )
            
            self.consumers[queue_name] = consumer_task
            self.message_handlers[queue_name] = handler
            
            logger.info(f"Started consumer for queue: {queue_name}")
            
        except Exception as e:
            logger.error(f"Failed to start consumer for queue {queue_name}: {str(e)}")
            raise
    
    async def _consume_messages(
        self, 
        queue: aio_pika.Queue, 
        handler: Callable[[PaymentMessage], None]
    ) -> None:
        """Consume messages from a queue."""
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        # Parse message
                        message_body = message.body.decode()
                        payment_message = PaymentMessage.model_validate_json(message_body)
                        
                        # Process message
                        await asyncio.create_task(
                            self._process_message(payment_message, handler)
                        )
                        
                    except Exception as e:
                        logger.error(f"Error processing message: {str(e)}")
                        # Reject message and requeue
                        await message.reject(requeue=True)
    
    async def _process_message(
        self, 
        payment_message: PaymentMessage, 
        handler: Callable[[PaymentMessage], None]
    ) -> None:
        """Process a payment message."""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(payment_message)
            else:
                handler(payment_message)
                
        except Exception as e:
            logger.error(f"Error in message handler: {str(e)}")
            raise
    
    async def stop_consumer(self, queue_name: str) -> None:
        """Stop consuming messages from a queue."""
        if queue_name in self.consumers:
            self.consumers[queue_name].cancel()
            del self.consumers[queue_name]
            del self.message_handlers[queue_name]
            logger.info(f"Stopped consumer for queue: {queue_name}")
    
    async def stop_all_consumers(self) -> None:
        """Stop all consumers."""
        for queue_name in list(self.consumers.keys()):
            await self.stop_consumer(queue_name)
    
    async def disconnect(self) -> None:
        """Disconnect from the MQ broker."""
        try:
            await self.stop_all_consumers()
            
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
                
            logger.info("Disconnected from MQ broker")
            
        except Exception as e:
            logger.error(f"Error disconnecting from MQ broker: {str(e)}")
    
    async def get_queue_info(self, queue_name: str) -> Dict[str, Any]:
        """Get information about a queue."""
        try:
            if queue_name not in self.queues:
                return {"error": "Queue not found"}
            
            queue = self.queues[queue_name]
            # Note: This is a simplified version. In production, you'd use RabbitMQ management API
            return {
                "queue_name": queue_name,
                "consumer_count": len(self.consumers.get(queue_name, [])),
                "active": queue_name in self.consumers
            }
            
        except Exception as e:
            logger.error(f"Error getting queue info: {str(e)}")
            return {"error": str(e)}


# Global MQ service instance
mq_service = MQService()
