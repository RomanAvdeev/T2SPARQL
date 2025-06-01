from fastapi import FastAPI, HTTPException
import os
import uvicorn
from t2sparql_dbpedia_model import DBpediaPipeline
from t2sprql_corporate_model import GPTEnhancedSemanticSearcher

# Получаем путь к директории текущего скрипта
script_dir = os.path.dirname(os.path.abspath(__file__))

# Создание приложения
app = FastAPI(title="TEXT2SPARQL API")

# API-ключ для OpenAI
api_key = ""

# Известные датасеты
KNOWN_DATASETS = [
    "https://text2sparql.aksw.org/2025/dbpedia/",
    "https://text2sparql.aksw.org/2025/corporate/"
]


@app.get("/generate-sparql-get")
async def generate_sparql_get(question: str, dataset: str):
    """
    GET-method to generate SPARQL
    """
    if dataset == KNOWN_DATASETS[0]:

        try:
            pipeline = DBpediaPipeline(api_key)
            sparql_query = pipeline.execute_pipeline(question)

            return {
                "dataset": dataset,
                "question": question,
                "query": sparql_query['sparql'].replace('\n', '')
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error during SPARQL generating: {str(e)} for dataset {dataset}"
            )

    elif dataset == KNOWN_DATASETS[1]:
        try:
            pipeline = GPTEnhancedSemanticSearcher(openai_api_key=api_key)

            pipeline.load_ttl(["prod-inst.ttl", "prod-vocab.ttl"])
            pipeline.create_chunks()
            pipeline.build_index()

            sparql_query = pipeline.generate_sparql(question, top_k=25)

            return {
                "dataset": dataset,
                "question": question,
                "query": sparql_query['generated_sparql'].replace('\n', '')
            }

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error during SPARQL generating: {str(e)} for dataset {dataset}"
            )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown dataset. Supported datasets: {', '.join(KNOWN_DATASETS)}"
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
