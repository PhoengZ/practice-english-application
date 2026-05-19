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
        self.add_batch_to_vector_db([word_id], [thai_text], [word_type])

    def add_batch_to_vector_db(self, ids, thai_texts, word_types):
        """Adds a batch of word translations to the vector database."""
        if not ids:
            return
            
        model = self._get_model()
        embeddings = model.encode(thai_texts).tolist()
        
        str_ids = [str(wid) for wid in ids]
        metadatas = [{"word_type": wt, "thai": tt} for wt, tt in zip(word_types, thai_texts)]
        
        self.collection.upsert(
            ids=str_ids,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def clear_all(self):
        """Clears all data from the vector collection."""
        self.client.delete_collection(name="thai_vocab")
        self.collection = self.client.get_or_create_collection(name="thai_vocab")
        print("✅ Vector database (ChromaDB) cleared.")

    def get_semantic_distractors(self, thai_text, word_type, count=3):
        """Fetches semantically similar distractors filtered by word type, ensuring unique Thai strings."""
        model = self._get_model()
        query_embedding = model.encode(thai_text).tolist()
        
        # Fetch a larger pool to account for potential duplicate Thai translations in the DB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=count + 15,
            where={"word_type": word_type}
        )
        
        distractors = []
        seen_thai = {thai_text} # Start with the correct answer to exclude it
        
        if results and results['metadatas']:
            for meta in results['metadatas'][0]:
                candidate_thai = meta['thai']
                if candidate_thai not in seen_thai:
                    distractors.append(candidate_thai)
                    seen_thai.add(candidate_thai)
                    if len(distractors) >= count:
                        break
        
        return distractors

# Singleton instance
vector_manager = VectorManager()
