# app/services/vector_store.py
import httpx
import chromadb
from chromadb.utils.embedding_functions import HuggingFaceEmbeddingFunction
from app.config import settings

class VectorStoreService:
    def __init__(self):
        # Initialize local persistent ChromaDB client
        self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
        
        # Configure Hugging Face cloud embedding engine
        self.embedding_function = HuggingFaceEmbeddingFunction(
            api_key=settings.HF_TOKEN,
            model_name="BAAI/bge-large-en-v1.5"
        )
        
        # Get or create our unique structural collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="github_projects",
            embedding_function=self.embedding_function
        )

    async def sync_github_repos(self, username: str) -> int:
        """Fetches public repositories from GitHub and stores their metadata + READMEs into ChromaDB."""
        if not settings.GITHUB_TOKEN:
            raise ValueError("GITHUB_TOKEN not found in environment configurations.")

        headers = {"Authorization": f"token {settings.GITHUB_TOKEN}"}
        url = f"https://api.github.com/users/{username}/repos"

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                print(f"Failed to fetch GitHub repos: {response.text}")
                return 0
            repos = response.json()

        documents = []
        metadatas = []
        ids = []

        for repo in repos:
            if repo.get("fork"): 
                continue # Skip forked repos to ensure we only index original work

            repo_name = repo.get("name")
            description = repo.get("description") or ""
            topics = ", ".join(repo.get("topics", []))
            
            # Formulate rich semantic text context for the embedding model to read
            context_string = f"Project: {repo_name}. Description: {description}. Tech Stack/Topics: {topics}."
            
            documents.append(context_string)
            metadatas.append({"source": "github", "repo_name": repo_name, "url": repo.get("html_url")})
            ids.append(f"gh_{repo.get('id')}")

        if documents:
            # ChromaDB automatically sends text to Hugging Face, gets vectors, and saves them locally
            self.collection.upsert(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
        return len(documents)

    def search_relevant_projects(self, job_description: str, limit: int = 2) -> list:
        """Queries ChromaDB using a job description to extract the most relevant engineering projects."""
        results = self.collection.query(
            query_texts=[job_description],
            n_results=limit
        )
        return results.get("metadatas", [[]])[0]