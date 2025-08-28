import json 
import faiss 
import numpy as np
from sentence_transformers import SentenceTransformer 

with open("playlist.json","r") as f:
  playlists = json.load(f)

model = SentenceTransformer("all-MiniLM-L6-v2")
playlist_names = [p["name"] for p in playlists]
embeddings = model.encode(playlist_names,normalize_embeddings=True)

dimension = embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)
index.add(np.array(embeddings))