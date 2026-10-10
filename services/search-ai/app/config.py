from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://agencia:agencia_dev@localhost:5432/agencia_viajes"
    booking_core_url: str = "http://localhost:8081/api/v1"
    catalog_cache_ttl_seconds: int = 60
    embedding_model: str = "BAAI/bge-small-es-v1.5"
    beto_enabled: bool = False
    scrape_urls: str = ""

    llm_provider: str = ""
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_timeout: float = 60.0
    agent_max_steps: int = 3

    @property
    def packages_endpoint(self) -> str:
        return f"{self.booking_core_url}/packages"

    @property
    def scrape_url_list(self) -> list[str]:
        return [url.strip() for url in self.scrape_urls.split(",") if url.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
