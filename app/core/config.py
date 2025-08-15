"""
Configuration settings for the Sanctions Screening Platform.

Author: Eon (Himanshu Shekhar)
Email: eonhimanshu@gmail.com
GitHub: https://github.com/eonn/sanctions-screening
Created: 2024
"""
import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "Sanctions Screening Platform"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # API
    api_prefix: str = "/api/v1"
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Database
    database_url: str = Field(
        default="sqlite:///./sanctions_screening.db",
        env="DATABASE_URL"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL"
    )
    
    # BERT Model
    bert_model_name: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        env="BERT_MODEL_NAME"
    )
    
    # Matching thresholds
    similarity_threshold: float = Field(
        default=0.85,
        env="SIMILARITY_THRESHOLD"
    )
    fuzzy_threshold: float = Field(
        default=0.8,
        env="FUZZY_THRESHOLD"
    )
    
    # Sanctions data sources
    sanctions_data_dir: str = Field(
        default="./data/sanctions",
        env="SANCTIONS_DATA_DIR"
    )
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Security
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    # Rate limiting
    rate_limit_per_minute: int = Field(
        default=100,
        env="RATE_LIMIT_PER_MINUTE"
    )
    
    # Message Queue (RabbitMQ) settings
    mq_host: str = Field(default="localhost", env="MQ_HOST")
    mq_port: int = Field(default=5672, env="MQ_PORT")
    mq_username: str = Field(default="guest", env="MQ_USERNAME")
    mq_password: str = Field(default="guest", env="MQ_PASSWORD")
    mq_virtual_host: str = Field(default="/", env="MQ_VIRTUAL_HOST")
    mq_exchange_name: str = Field(default="sanctions_screening", env="MQ_EXCHANGE_NAME")
    mq_payment_queue: str = Field(default="payment_screening", env="MQ_PAYMENT_QUEUE")
    mq_message_ttl: int = Field(default=86400000, env="MQ_MESSAGE_TTL")  # 24 hours in ms
    mq_max_queue_length: int = Field(default=10000, env="MQ_MAX_QUEUE_LENGTH")
    
    # Kafka settings
    kafka_bootstrap_servers: str = Field(
        default="localhost:9092", 
        env="KAFKA_BOOTSTRAP_SERVERS"
    )
    kafka_payment_topic: str = Field(
        default="payment_messages", 
        env="KAFKA_PAYMENT_TOPIC"
    )
    kafka_result_topic: str = Field(
        default="screening_results", 
        env="KAFKA_RESULT_TOPIC"
    )
    kafka_consumer_group: str = Field(
        default="sanctions-screening-group", 
        env="KAFKA_CONSUMER_GROUP"
    )
    
    # Risk thresholds for payment screening
    low_risk_threshold: float = Field(default=0.3, env="LOW_RISK_THRESHOLD")
    medium_risk_threshold: float = Field(default=0.7, env="MEDIUM_RISK_THRESHOLD")
    high_risk_threshold: float = Field(default=0.9, env="HIGH_RISK_THRESHOLD")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
