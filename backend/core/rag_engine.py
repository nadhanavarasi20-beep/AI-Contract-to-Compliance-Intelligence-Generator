import math
import re
from collections import Counter
from typing import List, Dict, Any, Tuple
from backend.models.schemas import Clause, SourceCitation

# Standard English stopwords
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't",
    "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having",
    "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how",
    "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its",
    "itself", "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on",
    "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't",
    "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's",
    "the", "their", "theirs", "them", "themselves", "then", "there", "there's", "these", "they", "they'd",
    "they'll", "they're", "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very",
    "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when",
    "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't",
    "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
}

class RAGEngine:
    """Pure Python Retrieval-Augmented Generation (RAG) vector index.
    Zero native DLL dependencies, zero external API quota consumption, 100% portable.
    """

    def __init__(self):
        self.contract_clauses: List[Clause] = []
        self.policy_clauses: List[Clause] = []
        self.vocab: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.contract_vectors: List[Dict[str, float]] = []
        self.is_indexed: bool = False

    def _tokenize(self, text: str) -> List[str]:
        """Extracts alphabetic and alphanumeric tokens."""
        tokens = re.findall(r'[a-zA-Z0-9]+', text.lower())
        return [t for t in tokens if len(t) > 1 and t not in STOP_WORDS]

    def _compute_tf_idf(self, tokens: List[str]) -> Dict[str, float]:
        """Calculates normalized TF-IDF vector."""
        if not tokens:
            return {}
        counts = Counter(tokens)
        total_tokens = len(tokens)
        vec = {}
        for token, count in counts.items():
            if token in self.idf:
                tf = count / total_tokens
                vec[token] = tf * self.idf[token]
        
        # Normalize vector length (L2 norm)
        norm = math.sqrt(sum(v * v for v in vec.values()))
        if norm > 0:
            for k in vec:
                vec[k] /= norm
        return vec

    def index_documents(self, contract_clauses: List[Clause], policy_clauses: List[Clause]):
        """Builds TF-IDF vector index across all contract and policy clauses."""
        self.contract_clauses = contract_clauses
        self.policy_clauses = policy_clauses

        doc_tokens_list = []
        for c in contract_clauses:
            doc_tokens_list.append(self._tokenize(f"{c.title} {c.text}"))
        for p in policy_clauses:
            doc_tokens_list.append(self._tokenize(f"{p.title} {p.text}"))

        total_docs = len(doc_tokens_list)
        if total_docs == 0:
            self.is_indexed = False
            return

        # Compute document frequency (DF)
        df_counter = Counter()
        for doc_tokens in doc_tokens_list:
            unique_tokens = set(doc_tokens)
            df_counter.update(unique_tokens)

        # Compute IDF
        self.idf = {}
        for token, df in df_counter.items():
            # Smooth IDF
            self.idf[token] = math.log((total_docs + 1) / (df + 1)) + 1.0

        # Build contract clause vectors
        self.contract_vectors = []
        for c in contract_clauses:
            tokens = self._tokenize(f"{c.title} {c.text}")
            self.contract_vectors.append(self._compute_tf_idf(tokens))

        self.is_indexed = True

    def retrieve_relevant_contract_clauses(
        self,
        query: str,
        top_k: int = 3,
        min_similarity: float = 0.04
    ) -> List[Tuple[Clause, float]]:
        """Retrieves top-K contract clauses matching the query string or policy rule."""
        if not self.is_indexed or not self.contract_clauses:
            return []

        query_tokens = self._tokenize(query)
        query_vec = self._compute_tf_idf(query_tokens)
        if not query_vec:
            return []

        scored_results: List[Tuple[int, float]] = []
        for idx, doc_vec in enumerate(self.contract_vectors):
            # Cosine similarity between normalized vectors = dot product
            sim = 0.0
            for token, q_val in query_vec.items():
                if token in doc_vec:
                    sim += q_val * doc_vec[token]
            if sim >= min_similarity:
                scored_results.append((idx, sim))

        # Sort descending by similarity
        scored_results.sort(key=lambda x: x[1], reverse=True)

        return [(self.contract_clauses[idx], score) for idx, score in scored_results[:top_k]]

    def create_citation(self, clause: Clause, doc_name: str, max_chars: int = 240) -> SourceCitation:
        """Constructs a validated SourceCitation object from a clause."""
        snippet = clause.text.strip()
        if len(snippet) > max_chars:
            snippet = snippet[:max_chars].rsplit(" ", 1)[0] + "..."
            
        return SourceCitation(
            document_name=doc_name,
            section_number=clause.section_num,
            section_title=clause.title,
            page_number=clause.page,
            snippet=snippet
        )
