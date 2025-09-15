"""
RAG Tool: Given a query, retrieve relevant recipes from FAISS index.
"""

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pandas as pd

class RecipeRetriever:
    def __init__(self, index_path, data_path, model_name="all-MiniLM-L6-v2"):
        self.index = faiss.read_index(index_path)
        self.df = pd.read_csv(data_path)
        self.model = SentenceTransformer(model_name)

    def query(self, text, k=3):
        embedding = self.model.encode([text])
        D, I = self.index.search(np.array(embedding).astype("float32"), k)
        return self.df.iloc[I[0]].to_dict(orient="records")
