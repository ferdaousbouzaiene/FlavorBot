from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pandas as pd
import os

def build_index(df, text_column="combined", model_name="all-MiniLM-L6-v2"):
    model = SentenceTransformer(model_name)
    embeddings = model.encode(df[text_column].tolist(), show_progress_bar=True)

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings).astype("float32"))

    return index, model, embeddings

def save_index(index, path="models/faiss.index"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    faiss.write_index(index, path)

def save_embeddings(embeddings, path="models/embeddings.npy"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.save(path, embeddings)

def save_dataframe(df, path="data/processed/recipes_cleaned.csv"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
