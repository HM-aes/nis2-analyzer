"""
Qdrant Vector Database Client
Manages NIS2 knowledge base storage and retrieval
Uses local on-disk mode - no server required.
"""

from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding
from django.conf import settings
import logging
import uuid

logger = logging.getLogger(__name__)


class NIS2QdrantClient:
    """
    Wrapper for Qdrant operations with NIS2 knowledge base.
    Uses fastembed (via qdrant-client[fastembed]) for lightweight embeddings.
    """

    def __init__(self):
        # Use local on-disk mode — no server needed
        local_path = getattr(settings, 'QDRANT_LOCAL_PATH', None)
        if local_path:
            self.client = QdrantClient(path=str(local_path))
        else:
            self.client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT
            )
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.vector_size = settings.QDRANT_VECTOR_SIZE
        self.embedding_model = TextEmbedding(settings.EMBEDDING_MODEL)

        # Ensure collection exists
        self._ensure_collection()

    def _ensure_collection(self):
        """Create collection if it doesn't exist"""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)

            if not exists:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")

    def add_document(self, text: str, metadata: dict) -> str:
        """
        Add a document chunk to Qdrant.

        Args:
            text: The text content to embed
            metadata: Dictionary with source, article, language, etc.

        Returns:
            point_id: UUID of the inserted point
        """
        try:
            vector = list(self.embedding_model.embed([text]))[0].tolist()

            point_id = str(uuid.uuid4())
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    'text': text,
                    **metadata
                }
            )

            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )

            return point_id

        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise

    def search(self, query: str, top_k: int = 5, filters: dict = None):
        """
        Semantic search in NIS2 knowledge base.

        Args:
            query: Search query text
            top_k: Number of results to return
            filters: Optional metadata filters (language, source, etc.)

        Returns:
            List of search results with text and metadata
        """
        try:
            query_vector = list(self.embedding_model.embed([query]))[0].tolist()

            search_filter = None
            if filters:
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                conditions = []
                for key, value in filters.items():
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=value))
                    )
                search_filter = Filter(must=conditions)

            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                query_filter=search_filter
            )

            return [
                {
                    'text': result.payload.get('text', ''),
                    'score': result.score,
                    'source': result.payload.get('source', ''),
                    'article': result.payload.get('article', ''),
                    'language': result.payload.get('language', ''),
                    'metadata': result.payload
                }
                for result in results
            ]

        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []

    def delete_collection(self):
        """Delete the entire collection (use with caution!)"""
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            logger.warning(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")

    def get_collection_info(self):
        """Get information about the collection"""
        try:
            return self.client.get_collection(collection_name=self.collection_name)
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return None
