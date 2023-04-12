import numpy as np
import app.logger as log
import faiss
from scipy import spatial

#calculates the cosine similarity between two embeddings.
def compute_similarity(embedding1, embedding2):
    log.debug("Calculating similarity.")
    try:
        sim = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
        return sim
    except Exception as exc:
        log.error(exc)
        return -99
        
def compute_similarity_faiss(embedding1, embedding2):
    log.debug("Calculating similarity using faiss.")
    try:
        x = np.array([embedding1]).astype(np.float32)
        q = np.array([embedding2]).astype(np.float32)
        index = faiss.index_factory(3, "Flat", faiss.METRIC_INNER_PRODUCT)
        index.ntotal
        faiss.normalize_L2(x)
        index.add(x)
        faiss.normalize_L2(q)
        distance, index = index.search(q, 5)
        print('Distance by FAISS:{}'.format(distance))
        return distance
    except Exception as exc:
        log.error(exc)
        return -99

def compute_similarity_spicy_cosine(embedding1, embedding2):
    log.debug("Calculating similarity scipy cosine.")
    try:
        result = 1 - spatial.distance.cosine(embedding1, embedding2)
        print('Distance by scipy cosine:{}'.format(result))
        return result
    except Exception as exc:
        log.error(exc)
        return -99