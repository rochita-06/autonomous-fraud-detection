from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(REPO_ROOT / ".env"), extra="ignore")

    # LLM — leave the key empty to run the deterministic rule-based agent
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"

    # API auth — leave empty to disable (dev mode). Set both in production.
    api_key: str = ""
    webhook_secret: str = ""

    # Storage
    database_url: str = "sqlite:///./fraud.db"


    # Graph — falls back to an in-memory graph when Neo4j is unreachable
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "fraudgraph"

    # Decision thresholds
    fraud_block_threshold: float = 0.8
    fraud_review_threshold: float = 0.5

    # Agent loop
    agent_max_steps: int = 8

    cors_origins: str = "*"

    data_dir: Path = REPO_ROOT / "data"


settings = Settings()
