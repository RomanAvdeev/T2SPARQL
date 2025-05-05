from openai import OpenAI
import os
from SPARQLWrapper import SPARQLWrapper, JSON
import re
import json
import faiss
from sentence_transformers import SentenceTransformer
from typing import Dict, Tuple, Optional, List
import requests
from urllib.parse import quote
import warnings
from urllib3.exceptions import InsecureRequestWarning
import t2sparql_dbpedia_prompts


class RAGSystem:
    def __init__(self, dataset_paths: List[str]):
        self.datasets = self._load_datasets(dataset_paths)
        self.all_data = self._preprocess_data()
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self._build_index()

    def _load_datasets(self, paths: List[str]) -> List[Dict]:
        """Загрузка всех датасетов из JSON файлов"""
        datasets = []
        for path in paths:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Обработка разных форматов датасетов
                if isinstance(data, dict) and 'questions' in data:
                    datasets.append(data)  # QALD-формат
                elif isinstance(data, list):
                    datasets.extend(data)  # LC-QuAD формат (список вопросов)
        return datasets

    def _preprocess_data(self) -> List[Dict]:
        """Объединение и предобработка данных из разных датасетов"""
        processed_data = []

        for dataset in self.datasets:

            if isinstance(dataset, dict) and 'questions' in dataset:
                # Обработка QALD-формата
                for question in dataset['questions']:
                    # Берем первый английский вопрос или первый вопрос любого языка
                    en_questions = [q['string'] for q in question['question'] if q['language'] == 'en']
                    question_text = en_questions[0] if en_questions else question['question'][0]['string']
                    processed_item = {
                        'question': question_text,
                        'query': question.get('query', {}).get('sparql', ''),
                        'dataset': 'qald',
                        'id': question.get('id', ''),
                        'languages': [q['language'] for q in question['question']]
                    }
                    processed_data.append(processed_item)

            elif isinstance(dataset, dict) and '_id' in dataset:
                # Обработка LC-QuAD формата (отдельные вопросы)

                processed_item = {
                    'question': dataset.get('corrected_question', ''),
                    'query': dataset.get('sparql_query', ''),
                    'dataset': 'lc_quad',
                    'id': dataset.get('_id', '')
                }
                processed_data.append(processed_item)

        return processed_data

    def _build_index(self):
        """Построение FAISS индекса для векторного поиска"""
        questions = [item['question'] for item in self.all_data]
        self.question_embeddings = self.model.encode(questions)

        dimension = self.question_embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(self.question_embeddings)

    def query(self, question: str, top_k: int = 3, threshold: Optional[float] = None,
              dataset_filter: Optional[str] = None, language: str = 'en') -> List[Dict]:
        """
        Поиск наиболее релевантных вопросов
        """
        query_embedding = self.model.encode([question])
        distances, indices = self.index.search(query_embedding, top_k)

        results = []
        for idx, dist in zip(indices[0], distances[0]):
            similarity = 1 - dist
            if threshold is None or similarity >= threshold:
                result = self.all_data[idx].copy()
                result['similarity_score'] = float(similarity)
                if dataset_filter is None or result['dataset'].lower() == dataset_filter.lower():
                    if language != 'en' and 'languages' in result:
                        if language not in result['languages']:
                            continue
                    results.append(result)

        return sorted(results, key=lambda x: x['similarity_score'], reverse=True)

    def get_context(self, question: str, top_k: int = 3, threshold: Optional[float] = None,
                    dataset_filter: Optional[str] = None, language: str = 'en') -> str:
        """
        Получение контекста в виде текста для заданного вопроса
        """
        similar_items = self.query(
            question,
            top_k=top_k,
            threshold=threshold,
            dataset_filter=dataset_filter,
            language=language
        )

        context = ""
        for item in similar_items:
            context += f"Question: {item['question']}\n"
            if item.get('query'):
                context += f"SPARQL: {item['query']}\n"
            context += "\n"
        return context.strip()

    def get_datasets_info(self) -> Dict:
        """Получение информации о загруженных датасетах"""
        qald_count = sum(1 for item in self.all_data if item['dataset'] == 'qald')
        lc_quad_count = sum(1 for item in self.all_data if item['dataset'] == 'lc_quad')

        return {
            'qald': {
                'size': qald_count,
                'description': 'QALD dataset with multilingual questions and SPARQL queries'
            },
            'lc_quad': {
                'size': lc_quad_count,
                'description': 'LC-QuAD dataset with English questions and SPARQL templates'
            }
        }


class DBpediaPipeline:
    def __init__(self, api_key: str, dbpedia_endpoint: str = "http://dbpedia.org/sparql",
                 NER_PROMPT: str = t2sparql_dbpedia_prompts.NER_PROMPT,
                 URI_GENERATION_PROMPT: str = t2sparql_dbpedia_prompts.URI_GENERATION_PROMPT,
                 SPARQL_GENERATION_PROMPT: str = t2sparql_dbpedia_prompts.SPARQL_GENERATION_PROMPT,
                 QUERY_REPAIR_PROMPT: str = t2sparql_dbpedia_prompts.QUERY_REPAIR_PROMPT,
                 QUESTION_CLARIFY: str = t2sparql_dbpedia_prompts.QUESTION_CLARIFY):

        self.client = OpenAI(api_key=api_key)
        self.sparql_endpoint = SPARQLWrapper(dbpedia_endpoint)
        self.sparql_endpoint.setReturnFormat(JSON)

        self.NER_PROMPT = NER_PROMPT
        self.URI_GENERATION_PROMPT = URI_GENERATION_PROMPT
        self.SPARQL_GENERATION_PROMPT = SPARQL_GENERATION_PROMPT
        self.QUERY_REPAIR_PROMPT = QUERY_REPAIR_PROMPT
        self.QUESTION_CLARIFY = QUESTION_CLARIFY
        self.rag = RAGSystem(['qald_9_plus_test_dbpedia.json', 'qald_9_plus_train_dbpedia.json', 'train-data.json'])

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

    def get_dbpedia(self, text: str, language: str = "en") -> Optional[Dict]:
        """Get entities from DBpedia Spotlight API"""

        # Отключаем предупреждения о небезопасных запросах
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        endpoint = f"https://api.dbpedia-spotlight.org/{language}/annotate"
        headers = {"Accept": "application/json"}
        params = {"text": text, "confidence": 0.5}

        try:
            response = requests.post(
                endpoint,
                headers=headers,
                data=params,
                verify=False  # Disable SSL verification
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            #print(f"DBpedia Spotlight API error: {e}")
            return None

    def uris(self, new_question: str) -> Tuple[Optional[str], Dict[str, str]]:
        """New entity extraction using DBpedia Spotlight"""


        spotlight_result = self.get_dbpedia(new_question)
        #print('Got spotlight result')

        if spotlight_result and "Resources" in spotlight_result:
            entities = {}
            tagged_parts = []
            remaining_text = new_question

            # Process each found entity
            for resource in sorted(spotlight_result["Resources"], key=lambda x: -int(x["@offset"])):
                entity_text = resource["@surfaceForm"]
                entity_type = resource["@types"].split(",")[0].split(":")[-1] if resource["@types"] else "thing"
                entity_uri = resource['@URI']

                # Replace in remaining text
                if entity_text in remaining_text:
                    entities[entity_text] = entity_uri
                    tagged_parts.append((remaining_text.index(entity_text),
                                        f"<{entity_text}>"))
                    remaining_text = remaining_text.replace(entity_text, "", 1)

            # Reconstruct tagged question
            if len(tagged_parts) > 1:

                #print('Making tagged question + URIs')

                # Sort by original position
                tagged_parts.sort()
                tagged_question = ""
                last_pos = 0

                for pos, tag in tagged_parts:
                    tagged_question += remaining_text[last_pos:pos] + tag
                    last_pos = pos

                tagged_question += remaining_text[last_pos:]

                return tagged_question, entities
            else:

              #print('Tagged entities <= 1')
              tagged_question, entities = self._original_extract_entities(new_question)
              if not tagged_question:
                return {"error": "Failed to extract entities"}
              return tagged_question, self._original_generate_uris(tagged_question, entities)
        else:
          #print('Spotlight result is empty')
          tagged_question, entities = self._original_extract_entities(new_question)
          if not tagged_question:
            return {"error": "Failed to extract entities"}
          return tagged_question, self._original_generate_uris(tagged_question, entities)

    def _original_extract_entities(self, question: str) -> Tuple[Optional[str], Dict[str, str]]:
        """Original GPT-4 based entity extraction (kept as fallback)"""
        prompt = f"""{self.NER_PROMPT}\n\nQuestion: {question}\nProvide output in the exact required format:"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert named entity recognizer for DBpedia questions. For each input question, follow this exact thinking process:

                        1. ANALYZE the question structure:
                          "In the question [quote question], we are asked: [paraphrase]"

                        2. IDENTIFY components:
                          - Main subject (class/resource)
                          - Properties/relationships
                          - Concrete entities (people/places/works)
                          - Constraints/conditions

                        3. EXTRACT entities:
                          "so we need to identify: [list entity types]"
                          "The entities are: [list specific entities]"

                        4. GENERATE intermediary question:
                          "So the intermediary_question is: [exact format as examples]"

                        Output MUST follow this exact template for every question:

                        Let's think step by step. In the question "[original question]", we are asked: "[paraphrased question]".
                        so we need to identify: [entity types].
                        The entities are: [specific entities].
                        So the intermediary_question is: [exact match to example format]"""

                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.0,
                max_tokens=400
            )

            full_response = response.choices[0].message.content.strip()
            #print(full_response)

            intermediary_match = re.search(
                r'So the intermediary_question is:\s*(.*?)$',
                full_response,
                re.MULTILINE
            )

            if not intermediary_match:
                #print("Error: Couldn't extract intermediary question from response")
                return None, {}

            tagged_question = intermediary_match.group(1).strip()

            entities = {}
            for match in re.finditer(r'<([^>]+)>([^<]+)</\1>', tagged_question):
                entity_type, entity_value = match.groups()
                entities[entity_value] = entity_type

            if not re.match(r'^Let\'s think step by step\.', full_response):
                #print("Error: Response doesn't follow DINSQL format")
                return None, {}

            return tagged_question, entities

        except Exception as e:
            #print(f"Error in entity extraction: {str(e)}")
            return None, {}

    def _original_generate_uris(self, tagged_question: str, entities: Dict[str, str]) -> Dict[str, str]:
        entity_list = "\n".join([f"- {value} ({type})" for value, type in entities.items()])
        prompt = f"{self.URI_GENERATION_PROMPT}\n\nTagged question: {tagged_question}\nEntities:\n{entity_list}\n\nDBpedia URIs:"

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """
                    DBpedia URI Conversion Expert - Entity to URI Mapping

                      Input Requirements:
                      1. Original question (for context)
                      2. Intermediary question with marked entities (<entity_type>)

                      Output Format:
                      - <tagged_entity> : full_DBpedia_URI (one per line)

                      URI Selection Rules:

                      1. Determining Entity Type:

                        a) RESOURCES (Specific named entities):
                            - Indicators: Proper nouns, specific instances
                            - Examples: <Blanche DuBois>, <Mid Wales>, <Python_(language)>
                            - Format: http://dbpedia.org/resource/Exact_Name
                              - Preserve original capitalization
                              - Replace spaces with underscores
                              - Keep special characters (parentheses, commas)
                              - Use official DBpedia names (check redirects)

                        b) CLASSES (Categories/Types):
                            - Indicators: Generic categories, answers "what kind?"
                            - Examples: <play>, <company>, <city>
                            - Format: http://dbpedia.org/ontology/ProperCase
                              - Always singular form
                              - Capitalize first letter
                              - Use most specific available class

                        c) PROPERTIES (Relationships):
                            - Indicators: Connects entities, shows relationships
                            - Examples: <founded by>, <alma mater>, <developer>
                            - Selection Priority:
                              1. Ontology properties (preferred):
                                  - Format: http://dbpedia.org/ontology/lowercase_property
                                  - More stable, better defined semantics
                              2. Generic properties (fallback):
                                  - Format: http://dbpedia.org/property/lowercase_property
                                  - Used when no ontology property exists
                            - Transformation rules:
                              - Convert to lowercase
                              - Replace spaces with underscores
                              - Use natural property names (e.g., 'alma mater' : 'almaMater')
                """},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=500
            )
            uri_text = response.choices[0].message.content

            uris = {}
            for line in uri_text.split('\n'):
                if line.strip() and ':' in line:
                    parts = line.split(':', 1)
                    entity = parts[0].strip().strip('-').strip()
                    uri = parts[1].strip()
                    uris[entity] = uri

            return uris
        except Exception as e:
            #print(f"Error in URI generation: {str(e)}")
            return {}

    def generate_sparql(self, original_question: str, tagged_question: str, uris: Dict[str, str]) -> Optional[str]:

        uri_mapping = "\n".join([f"- <{entity}> : {uri}" for entity, uri in uris.items()])
        URI = [uri for entity, uri in uris.items()]

        dbpedia_neighbors = [self.get_dbpedia_neighbors(f'{entity_url}') for entity_url in URI]

        # for each URI got maximum 10 neighbours, but total amount of neighbours must be <= 30

        max_neighbours_per_entity = 30 // len(URI)

        dbpedia_neighbors_uris = []

        for neighbour_dict in dbpedia_neighbors:
            dbpedia_neighbors_uris += list(neighbour_dict.values())[:max_neighbours_per_entity]

        context_from_rag = self.rag.get_context(original_question, top_k=7)

        prompt = f"""{self.SPARQL_GENERATION_PROMPT}\n\n
                Input:
                Original Question: "{original_question}"
                Question with Entities: "{tagged_question}"
                DBpedia URIs:
                {uri_mapping}
                dbpedia_neighbors:
                {' '.join(dbpedia_neighbors_uris)}
                Similar questions from datasets and correct SPARQL for them for the better context: {context_from_rag}
                """

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a precise SPARQL query generator that follows DINSQL-style reasoning with URI generation capabilities. Strictly follow these rules:

                          0. OUTPUT CONTROL:
                          - Return ONLY the SPARQL query in a clean code block OR "INVALID_INPUT"
                          - Absolutely NO explanations, thought processes, or disclaimers
                          - If generating URIs, do so SILENTLY without commentary

                          1. URI HANDLING RULES:
                          1.1 For provided URIs:
                          - Use EXACTLY as given
                          - Never modify existing URIs
                          1.2 For missing URIs:
                          - Generate ONLY when ALL conditions are met:
                            * The URI is CRITICAL for query execution
                            * The needed URI is OBVIOUS (e.g., dbo:birthDate for person)
                            * The URI follows standard DBpedia/Wikidata patterns
                          - Generation priority:
                            * Properties > Classes > Entities
                            * Never generate entity URIs (only properties/classes)

                          2. QUERY CONSTRUCTION:
                          2.1 Structure analysis:
                          - Parse original question intent
                          - Map all tagged relationships
                          - Incorporate ALL provided URIs
                          2.2 Transformation rules:
                          - Preserve exact entity relationships
                          - Maintain variable binding consistency
                          - Apply proper class restrictions (rdf:type)
                          2.3 Best practices:
                          - Use SELECT/ASK appropriately
                          - Include DISTINCT when needed
                          - Use proper SPARQL syntax

                          3. VALIDATION CHECKS:
                          - All provided URIs must appear exactly
                          - Generated URIs must follow standard patterns
                          - Variables must be properly joined
                          - Query must execute as intended

                          4. FAILURE MODE:
                          - Return "INVALID_INPUT" ONLY if:
                            * Missing CRITICAL entity URIs
                            * Question is fundamentally unanswerable
                            * Syntax cannot be fixed

                          5. Output format:
                            - Always begin with a 'Thought Process:' section explaining:
                              * How you interpreted the question
                              * Why you chose specific patterns
                              * How variables connect
                            - Provide the SPARQL query in a clean code block

                          Examples of allowed URI generation:
                          - "birth year" → dbo:birthYear
                          - "company founder" → dbo:founder
                          - "chemical formula" → dbo:formula

                          Examples of forbidden generation:
                          - Inventing entity URIs (e.g., dbr:SomePerson)
                          - Guessing non-obvious properties
                          - Creating non-standard prefixes

                          REMEMBER:
                          - When in doubt, GENERATE rather than fail
                          - Better a working query than INVALID_INPUT"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.0,
                max_tokens=800
            )

            full_response = response.choices[0].message.content.strip()
            sparql_match = re.search(r'SPARQL:\s*(.*?)$', full_response, re.DOTALL)
            if not sparql_match:
              correction_response = self.client.chat.completions.create(
              model="gpt-4",
              messages=[
                {
                    "role": "system",
                    "content": """You are a SPARQL error correction expert. When given a failed generation attempt:
                    1. Analyze ALL problems
                    2. Explain each issue clearly
                    3. Return a WORKING SPARQL query
                    4. Use ONLY the provided URIs
                    5. Maintain strict DINSQL standards"""
                },
                {
                    "role": "user",
                    "content": f"""Please analyze and fix the SPARQL generation error for this task:

                                    Original Question: "{original_question}"
                                    Tagged Question: "{tagged_question}"
                                    Provided URIs:
                                    {uri_mapping}

                                    Required Actions:
                                    1. Identify ALL issues in the failed generation attempt
                                    2. Explain each problem clearly
                                    3. Provide the CORRECTED SPARQL query
                                    4. Ensure the fixed query:
                                      - Uses all provided URIs correctly
                                      - Matches the question intent
                                      - Has proper syntax and structure

                                    Agent reasoning:
                                    {full_response}

                                    Return your response in EXACTLY this format:

                                    ANALYSIS:
                                    1. [Issue 1 description]
                                    2. [Issue 2 description]...

                                    CORRECTED SPARQL:
                                    [The fully corrected SPARQL query here]"""
                }
              ],
              temperature=0.0,
              max_tokens=1000
              )

              correction_text = correction_response.choices[0].message.content

              # Извлекаем исправленный SPARQL
              corrected_sparql = re.search(r'CORRECTED SPARQL:\s*(.*?)$', correction_text, re.DOTALL) or \
                                re.search(r'```sparql\n(.*?)```', correction_text, re.DOTALL)
              if corrected_sparql:
                  return corrected_sparql.group(1).strip()
              else:
                  return None
            else:
                sparql_query = sparql_match.group(1).strip()
                return sparql_query

        except Exception as e:
           return None

    def postprocess_query(self, query) -> str:
        query = re.sub(r'^\s*#.*$', '', query, flags=re.MULTILINE)
        return query.strip()

    def validate_query(self, query):
      try:
          self.sparql_endpoint.setQuery(query)
          results = self.sparql_endpoint.query().convert()

          # Проверка на пустые результаты
          if 'boolean' in results.keys():
              if isinstance(results['boolean'], bool):
                  return True, None
          elif 'results' in results:
              if len(results['results']['bindings']) == 0:
                  return False, "Query executed successfully but returned empty results. Please regenerate the query with different parameters or conditions."
          return True, None

      except Exception as e:
          error_msg = re.sub(r"Endpoint returned:.*", "", str(e)).strip()
          return False, error_msg

    def repair_query(self, original_query, error, context):
        prompt = self.QUERY_REPAIR_PROMPT.format(
          error=error,
          original_query=original_query,
          original_question=context['original_question'],
          tagged_question=context['tagged_question'],
          uris="\n".join([f"- {k}: {v}" for k,v in context['uris'].items()])
        )
        try:
          response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": """You are a SPARQL repair expert. Apply these strategies:
                  1. For empty results:
                    - Find alternative URIs keeping original meaning
                    - Use dbo: instead of dbp: when possible
                    - Try superclasses/subproperties
                  2. For syntax errors:
                    - Fix exactly what's broken
                    - Never change working parts
                  Output ONLY the fixed query"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,  # Немного креативности для альтернативных URI
            max_tokens=600
            )
          return response.choices[0].message.content.strip()

        except Exception as e:
            return None

    def get_dbpedia_neighbors(self, entity_url: str):
        """
        Extracts all neighbours of an entity in DBpedia knowledge graph.

        Args:
            entity_url (str): URL сущности в DBpedia (например, "http://dbpedia.org/resource/Danielle_Steel")
        Returns:
            dict: Словарь, где ключи - имена связанных сущностей, значения - их URL в DBpedia
        """
        # Проверяем и корректируем URL

        if not entity_url.startswith("http://dbpedia.org/resource/"):
            entity_url = f"http://dbpedia.org/resource/{entity_url.split('/')[-1]}"


        # SPARQL запрос для получения всех соседей
        sparql_query = f"""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT DISTINCT ?property ?neighbor ?neighborLabel WHERE {{
              <{entity_url}> ?property ?neighbor .
              FILTER (isURI(?neighbor) && STRSTARTS(STR(?neighbor), "http://dbpedia.org/resource/"))
              OPTIONAL {{
                ?neighbor rdfs:label ?neighborLabel .
                FILTER (LANG(?neighborLabel) = "en")
              }}
            }}
            LIMIT 30
            """

        # Параметры запроса
        params = {
            'query': sparql_query,
            'format': 'json'
        }

        headers = {
            'Accept': 'application/sparql-results+json'
        }

        endpoint_url = "https://dbpedia.org/sparql"

        try:
            response = requests.get(endpoint_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            results = response.json()

            neighbors = {}

            for binding in results["results"]["bindings"]:

              if len(list(neighbors.keys())) <= 10:
                neighbor_url = binding["neighbor"]["value"]

                # Используем URL как имя, если нет метки
                neighbor_name = binding.get("neighborLabel", {}).get("value", neighbor_url.split("/")[-1].replace("_", " "))
                neighbors[neighbor_name] = neighbor_url
              else:
                break

            return neighbors

        except Exception as e:
            return {}

    def query_rewriting(self, question: str) -> str:
        prompt = self.QUESTION_CLARIFY.format(question=question)

        try:
          response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": """You are a SPARQL repair expert. Apply these strategies:
                  1. Try to change the input question as little as possible
                  2. If the given question is correct (not ambiguous) print it without changes.
                  3. As the output put only the clarified question without writing the given one."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=600
            )
          return response.choices[0].message.content.strip()

        except Exception as e:
            return None

    def execute_pipeline(self, question: str, max_retries: int = 2) -> Dict:

        # Step 1) Translating
        en_question = self.translate_to_english(question)
        print('English question: ', en_question)

        # Step 2) Query rewriting
        rewritten_question = self.query_rewriting(en_question)
        print('Rewritten question: ', rewritten_question)

        # Step 3) Entity recognition
        tagged_question, entities_URI = self.uris(rewritten_question)

        # Step 4) SPARQL generation
        sparql = self.generate_sparql(en_question, tagged_question, entities_URI)

        if not sparql:
            return {"error": "Failed to generate SPARQL", "tagged_question": tagged_question, "uris": entities_URI}

        # Step 5) SPARQL repairing
        for attempt in range(max_retries + 1):
            is_valid, error = self.validate_query(sparql)
            if is_valid:
                return {
                    "status": "success",
                    "tagged_question": tagged_question,
                    "uris": entities_URI,
                    "sparql": sparql
                }

            if attempt < max_retries:
                context = {
                    "original_question": en_question,
                    "tagged_question": tagged_question,
                    "uris": entities_URI
                }
                repaired_query = self.repair_query(sparql, error, context)
                if repaired_query and repaired_query != sparql:
                    continue

            return {
                "status": "error",
                "error": error,
                "tagged_question": tagged_question,
                "uris": entities_URI,
                "sparql": sparql
            }