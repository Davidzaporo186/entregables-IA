"""RAG local verificable. Backend opcional FAISS+embeddings; fallback TF-IDF sin internet."""
import json
import os
from functools import lru_cache
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CORPUS = Path(__file__).resolve().parents[1] / 'data' / 'fuentes_rag.json'
EMBEDDING_MODEL = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'


@lru_cache(maxsize=1)
def _documents():
    docs = json.loads(CORPUS.read_text(encoding='utf-8'))
    if not docs or any(not all(d.get(k) for k in ('id','titulo','texto','url')) for d in docs):
        raise ValueError('Corpus RAG inválido')
    return docs


@lru_cache(maxsize=1)
def _lexical_index():
    docs = _documents()
    tfidf = TfidfVectorizer(strip_accents='unicode', ngram_range=(1, 2))
    matrix = tfidf.fit_transform([d['titulo'] + ' ' + d['texto'] for d in docs])
    return tfidf, matrix


@lru_cache(maxsize=1)
def _semantic_index():
    # Requiere `pip install -r requirements-rag.txt` y descarga inicial del modelo.
    import faiss
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(EMBEDDING_MODEL)
    docs = _documents()
    vectors = model.encode([d['titulo'] + '. ' + d['texto'] for d in docs],
                           normalize_embeddings=True, convert_to_numpy=True).astype('float32')
    idx = faiss.IndexFlatIP(vectors.shape[1])
    idx.add(vectors)
    return model, idx


def search_docs(query, top_k=3, backend=None):
    if not isinstance(query, str) or not query.strip():
        return []
    docs = _documents()
    top_k = max(1, min(int(top_k), len(docs), 10))
    backend = (backend or os.getenv('RAG_BACKEND', 'tfidf')).lower()
    if backend == 'faiss':
        try:
            model, idx = _semantic_index()
        except (ImportError, OSError) as exc:
            raise RuntimeError('Instala requirements-rag.txt y descarga el modelo para RAG_BACKEND=faiss') from exc
        q = model.encode([query], normalize_embeddings=True, convert_to_numpy=True).astype('float32')
        scores, ids = idx.search(q, top_k)
        results = [(int(i), float(s)) for i,s in zip(ids[0], scores[0]) if i >= 0 and s > 0]
    elif backend == 'tfidf':
        vectorizer, matrix = _lexical_index()
        scores = cosine_similarity(vectorizer.transform([query]), matrix).ravel()
        results = [(int(i), float(scores[i])) for i in np.argsort(scores)[::-1][:top_k] if scores[i] > 0]
    else:
        raise ValueError('Backend RAG no válido: tfidf o faiss')
    return [{**docs[i], 'score': round(s, 4), 'backend': backend} for i,s in results]
