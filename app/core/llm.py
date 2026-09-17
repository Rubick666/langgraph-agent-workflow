from langchain_ollama import ChatOllama

from app.core.config import settings

llm = ChatOllama(
    model=settings.ollama_model,
    base_url=settings.ollama_host,
    temperature=0.2,
    num_predict=120,
    num_ctx=1024,
)