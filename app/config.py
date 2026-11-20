from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://intake:intake@localhost:5432/intake"
    data_dir: str = "./data"
    embed_model: str = "Snowflake/snowflake-arctic-embed-s"
    anthropic_api_key: str = ""

    # Cost controls for /query
    claude_model: str = "claude-haiku-5-5"
    query_max_tokens: int = 500        # cap on the length of an answer
    query_top_k: int = 8               # chunks sent to Claude per question
    max_queries_per_day: int = 200     # hard stop against runaway loops
    # Cost controls for /extract (the whole form is sent once, and the answer is a JSON record)
    extract_max_tokens: int = 1500
    max_extractions_per_day: int = 100
    # USD per million tokens for claude_model (Haiku 5.5, prompts up to 100K tokens).
    # Used only for the cost estimate; update if you change the model.
    price_in_per_mtok: float = 0.10
    price_out_per_mtok: float = 0.50


settings = Settings()
