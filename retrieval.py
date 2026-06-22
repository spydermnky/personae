"""
Turns a suspect's case file into searchable facts and retrieves only 
the ones relevant to a given question (embedding-based retrieval / RAG).
"""

import numpy as np
from sentence_transformers import SentenceTransformer

# Small local embedding model, turns text into vectors
_model = SentenceTransformer("all-MiniLM-L6-v2")

def _embed(texts):
    # Turn a list of strings into vectors
    # normalize_embeddings makes the dot product equal cosine similarity
    return _model.encode(texts, normalize_embeddings=True)

def parse_case_file(path):
    # Split a file into chunks 
    chunks = []
    current_section = ""
    with open(path, "r") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            if line.startswith("## "):
                current_section = line[3:].strip()
            elif line.startswith("# "):
                continue
            elif line.startswith("- "):
                chunks.append({
                    "text": line[2:].strip(),
                    "section": current_section,
                    "guarded": "GUARDED" in current_section.upper(),
                })
            elif chunks:
                chunks[-1]["text"] += " " + line.strip()
    return chunks

class SuspectMemory:
    ALWAYS_PREFIXES = ("Who you are", "Your alibi")

    def _is_always(self, section):
        return any(section.startswith(p) for p in self.ALWAYS_PREFIXES)

    def __init__(self, case_path):
        self.chunks = parse_case_file(case_path)

        # Split facts into "always in context" vs "retrieve by relevance"
        self.always = []
        self.retrievable = []
        for c in self.chunks:
            if self._is_always(c["section"]) or c["guarded"]:
                self.always.append(c)
            else:
                self.retrievable.append(c)
        
        # Pre-compute vectors for retrieval
        if self.retrievable:
            self.embeddings = _embed([c["text"] for c in self.retrievable])
        else:
            self.embeddings = None
        
    def relevant_facts(self, question, top_k=4):
        # Return the always_on facts plus top_k relevant retrievable facts
        retrieved = []
        if self.embeddings is not None:
            q = _embed([question])[0]
            scores = self.embeddings @ q
            top = np.argsort(scores)[::-1][:top_k]
            retrieved = [self.retrievable[i] for i in top]
        return self.always + retrieved