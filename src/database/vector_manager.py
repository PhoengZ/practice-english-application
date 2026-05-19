import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_PATH = os.path.join(BASE_DIR, "data", "chroma_db")
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

class VectorManager:
    def __init__(self):
        self.client = None
        self.collection = None
        self.model = None

    def _get_collection(self):
        """Lazy initializer for ChromaDB client and collection."""
        if self.collection is None:
            try:
                import chromadb
                self.client = chromadb.PersistentClient(path=CHROMA_PATH)
                self.collection = self.client.get_or_create_collection(name="thai_vocab")
            except Exception as e:
                print(f"Error initializing ChromaDB: {e}")
                raise
        return self.collection

    def _get_model(self):
        """Lazy initializer for the embedding model."""
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                print(f"Loading embedding model: {MODEL_NAME}...")
                self.model = SentenceTransformer(MODEL_NAME)
            except Exception as e:
                print(f"Error loading SentenceTransformer: {e}")
                raise
        return self.model

    def add_to_vector_db(self, word_id, thai_text, word_type):
        """Adds a single word translation to the vector database."""
        self.add_batch_to_vector_db([word_id], [thai_text], [word_type])

    def add_batch_to_vector_db(self, ids, thai_texts, word_types):
        """Adds a batch of word translations to the vector database."""
        if not ids:
            return
            
        collection = self._get_collection()
        model = self._get_model()
        embeddings = model.encode(thai_texts).tolist()
        
        str_ids = [str(wid) for wid in ids]
        metadatas = [{"word_type": wt, "thai": tt} for wt, tt in zip(word_types, thai_texts)]
        
        collection.upsert(
            ids=str_ids,
            embeddings=embeddings,
            metadatas=metadatas
        )

    def clear_all(self):
        """Clears all data from the vector collection."""
        if self.client is None:
            import chromadb
            self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        
        try:
            self.client.delete_collection(name="thai_vocab")
        except Exception:
            # Collection might not exist yet
            pass
            
        self.collection = self.client.get_or_create_collection(name="thai_vocab")
        print("✅ Vector database (ChromaDB) cleared.")

    def get_semantic_distractors(self, thai_text, word_type, count=3):
        """Fetches semantically similar distractors filtered by word type, ensuring unique Thai strings."""
        try:
            collection = self._get_collection()
            model = self._get_model()
        except Exception:
            # Silently fail and allow fallback to SQL in calling code
            return []

        query_embedding = model.encode(thai_text).tolist()
        
        # Fetch a larger pool to account for potential duplicate Thai translations in the DB
        results = collection.query(
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
