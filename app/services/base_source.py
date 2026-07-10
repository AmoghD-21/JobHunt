# app/services/base_source.py
from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel, HttpUrl

class AggregatedJobSchema(BaseModel):
    title: str
    company: str
    location: str | None = None
    description: str
    source_url: HttpUrl
    source_platform: str

class BaseJobSource(ABC):
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Returns the identifier name of the source (e.g., 'remotive')."""
        pass

    @abstractmethod
    async def fetch_jobs(self, keyword: str | None = None) -> List[AggregatedJobSchema]:
        """Fetches raw data from the third-party provider and maps it safely to our common schema."""
        pass