from typing import Dict, Optional
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
from faiss import IndexFlatIP
from rdflib import Graph, URIRef, BNode


class GPTEnhancedSemanticSearcher:
    def __init__(self, openai_api_key: str):
        self.client = OpenAI(api_key=openai_api_key)
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.graph = None
        self.chunks = []
        self.metadata = []
        self.index = None

    def translate_to_english(self, text):
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise translation engine. Translate the input to English exactly, preserving: "
                               "1. All named entities (names, places, titles) "
                               "2. Technical terms "
                               "3. Question structure "
                               "Output ONLY the translation without commentary."
                },
                {
                    "role": "user",
                    "content": f"Translate this to English exactly:\n\n{text}"
                }
            ],
            temperature=0.1,
            max_tokens=500
        )
        return response.choices[0].message.content.strip()

    def load_ttl(self, file_paths):
        self.graph = Graph()
        for path in file_paths:
            self.graph.parse(path, format="turtle")

    def create_chunks(self):
        self.chunks = []
        self.metadata = []

        for entity in set(self.graph.subjects()):
            if isinstance(entity, (URIRef, BNode)):
                desc = "\n".join([f"{self._uri_to_sparql(p)} {self._uri_to_sparql(o)}"
                                for _, p, o in self.graph.triples((entity, None, None))])
                self.chunks.append(f"Entity: {self._uri_to_sparql(entity)}\n{desc}")
                self.metadata.append({"source": str(entity)})

    def _uri_to_sparql(self, uri):
        if isinstance(uri, URIRef):
            for prefix, ns in self.graph.namespaces():
                if uri.startswith(ns):
                    return f"{prefix}:{uri.replace(ns, '')}"
        return f"<{uri}>"

    def build_index(self):
        self.embeddings = self.model.encode(self.chunks, show_progress_bar=True)
        self.index = IndexFlatIP(self.embeddings.shape[1])
        self.index.add(self.embeddings)

    def search(self, query: str, top_k: int = 3):
        query_embedding = self.model.encode(query)
        query_embedding = np.array(query_embedding, dtype=np.float32).reshape(1, -1)

        faiss.normalize_L2(query_embedding)
        faiss.normalize_L2(self.embeddings)

        distances, indices = self.index.search(query_embedding, top_k)

        return [{
            "text": self.chunks[idx],
            "metadata": self.metadata[idx],
            "score": float(distances[0][i])
        } for i, idx in enumerate(indices[0])]

    def generate_sparql(self, original_question: str, top_k: int = 3) -> Optional[dict]:
        # Шаг 1: Перевод вопроса
        translated_question = self.translate_to_english(original_question)

        # Шаг 2: Семантический поиск
        rag_results = self.search(translated_question, top_k)
        context = "\n".join([res['text'] for res in rag_results])

        # Шаг 3: Генерация SPARQL
        namespaces = [f"PREFIX {prefix}: <{ns}>" for prefix, ns in self.graph.namespaces()]

        prompt = f"""
        It is required to generate a SPARQL query for a specific knowledge graph.
        The graph is loaded from TTL files and has the following characteristics:

        {len(namespaces)} registered namespace:
        {chr(10).join(namespaces)}

        A question for generating a query:
        "{translated_question}"

        Relevant graph fragments:
        {context}

        Strict requirements:
        1. Use ONLY prefixes and URIs from the given context
        2. Don't invent new properties/classes.
        3. Match the exact meaning of the question
        4. Output format:
        ```sparql
        YOUR_QUERY
        ```

        Additional notes:
        - If the issue cannot be resolved based on the context, return "INVALID"
        - Always filter by rdf:type if the entity class is known
        - Use DISTINCT to avoid duplicates
        - Optimize the query for fast execution
        """

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert SPARQL query generator. Your task is to create a working query for a specific knowledge graph.

                    Critical rules:
                    1. Follow the ontology exactly from the context
                    2. Keep the original namespace prefixes
                    3. Verify the validity of all URIs used
                    4. Optimize the query structure

                    The algorithm of operation:
                    1. Analyze the question and the context
                    2. Identify all necessary URIs
                    3. Build the appropriate query pattern
                    4. Verify compliance with the requirements
                    5. Return a clean SPARQL or "INVALID"

                    """
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=1000
        )

        raw_output = response.choices[0].message.content.strip()

        if "```sparql" in raw_output:
            generated_sparql = raw_output.split("```sparql")[1].split("```")[0].strip()
        else:
            generated_sparql = raw_output

        return {
            "generated_sparql": generated_sparql
        }
