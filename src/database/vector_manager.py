import os
import sqlite3
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_PATH = os.path.join(BASE_DIR, "data", "chroma_db")
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

class VectorManager:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = self.client.get_or_create_collection(name="thai_vocab")
        self.model = None # Lazy load model

    def _get_model(self):
        if self.model is None:
            print(f"Loading embedding model: {MODEL_NAME}...")
            self.model = SentenceTransformer(MODEL_NAME)
        return self.model

    def add_to_vector_db(self, word_id, thai_text, word_type):
        """Adds a single word translation to the vector database."""
        model = self._get_model()
        embedding = model.encode(thai_text).tolist()
        
        self.collection.upsert(
            ids=[str(word_id)],
            embeddings=[embedding],
            metadatas=[{"word_type": word_type, "thai": thai_text}]
        )

    def get_semantic_distractors(self, thai_text, word_type, count=3):
        """Fetches semantically similar distractors filtered by word type."""
        model = self._get_model()
        query_embedding = model.encode(thai_text).tolist()
        
        # We fetch more than count to allow filtering out the original word
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=count + 5,
            where={"word_type": word_type}
        )
        
        distractors = []
        if results and results['metadatas']:
            for meta in results['metadatas'][0]:
                if meta['thai'] != thai_text:
                    distractors.append(meta['thai'])
                    if len(distractors) >= count:
                        break
        
        return distractors

# Singleton instance
vector_manager = VectorManager()
