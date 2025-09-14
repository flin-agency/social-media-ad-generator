"""Configuration management for the Social Media Ad Generator."""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config(BaseSettings):
    """Application configuration."""

    # API Configuration
    gemini_api_key: str = Field(..., env="GEMINI_API_KEY")

    # Agent Configuration
    agent_name: str = Field("SocialMediaAdGenerator", env="AGENT_NAME")
    agent_version: str = Field("1.0.0", env="AGENT_VERSION")

    # Image Processing Configuration
    max_image_size_mb: int = Field(10, env="MAX_IMAGE_SIZE_MB")
    supported_formats: str = Field("JPEG,PNG,WEBP", env="SUPPORTED_FORMATS")
    output_resolution: str = Field("1080x1920", env="OUTPUT_RESOLUTION")

    # Generation Configuration
    max_generation_time_seconds: int = Field(90, env="MAX_GENERATION_TIME_SECONDS")
    concurrent_generations: int = Field(4, env="CONCURRENT_GENERATIONS")
    retry_attempts: int = Field(3, env="RETRY_ATTEMPTS")

    # Logging Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("logs/agent.log", env="LOG_FILE")

    @property
    def supported_formats_list(self) -> List[str]:
        """Get supported image formats as a list."""
        return [fmt.strip().upper() for fmt in self.supported_formats.split(",")]

    @property
    def output_width_height(self) -> tuple[int, int]:
        """Get output resolution as width, height tuple."""
        width, height = self.output_resolution.split("x")
        return int(width), int(height)

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


# Global configuration instance
config = Config()