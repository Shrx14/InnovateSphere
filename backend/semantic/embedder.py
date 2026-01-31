from sentence_transformers import SentenceTransformer

class Embedder:
    _instance = None
    _model = None

    @classmethod
    def get_embedding_model(cls):
        if cls._model is None:
            cls._model = SentenceTransformer('all-MiniLM-L6-v2')
        return cls._model

    @classmethod
    def embed_texts(cls, texts):
        model = cls.get_embedding_model()
        embeddings = model.encode(texts)
        return embeddings.tolist()
