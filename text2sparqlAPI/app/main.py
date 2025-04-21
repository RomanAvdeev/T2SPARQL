from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from transformers import pipeline

# Получаем путь к директории текущего скрипта
script_dir = os.path.dirname(os.path.abspath(__file__))

# Переходим на уровень выше
parent_dir = os.path.dirname(script_dir)

# Получаем путь к JSON
path_to_json = os.path.join(parent_dir, 'queries.json')

# Создание приложения
app = FastAPI(title="TEXT2SPARQL API")

# Загрузка предобученной модели (пример для HuggingFace)
# В реальном проекте замените на свою модель
try:
    text2sparql_model = pipeline("text2text-generation", model="InfAI/flan-t5-text2sparql-naive")
except:
    # Заглушка, если модель не загрузилась
    text2sparql_model = None

# Класс для входных данных
class QueryRequest(BaseModel):
    question: str
    dataset: str

# Известные датасеты
KNOWN_DATASETS = [
    "DBPedia",
    "LC_QUAD 2.0"
]

@app.get("/")
async def root():
    return {"message": "TEXT2SPARQL API is running"}

@app.post("/generate-sparql")
async def generate_sparql(request: QueryRequest):
    """
    Генерирует SPARQL-запрос из вопроса на естественном языке
    
    Параметры:
    - question: Вопрос на естественном языке (например, "Какие города есть в Германии?")
    - dataset: URL поддерживаемого датасета
    
    Возвращает:
    - Сгенерированный SPARQL-запрос
    """
    if request.dataset not in KNOWN_DATASETS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown dataset. Supported datasets: {', '.join(KNOWN_DATASETS)}"
        )
    
    if not text2sparql_model:
        raise HTTPException(
            status_code=503,
            detail="Model is not available"
        )
    
    try:
        # Формируем входной текст для модели
        input_text = f"Create SPARQL Query: {request.question}"
        
        # Генерация SPARQL запроса (реальная реализация зависит от вашей модели)
        generated = text2sparql_model()
        
        sparql_query = generated[0]['generated_text']
        
        return {
            "dataset": request.dataset,
            "question": request.question,
            "sparql_query": sparql_query,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating SPARQL: {str(e)}"
        )

@app.get("/generate-sparql-get")
async def generate_sparql_get(question: str, dataset: str):
    """
    GET-версия генератора SPARQL (для простого тестирования)
    """
    if dataset not in KNOWN_DATASETS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown dataset. Supported datasets: {', '.join(KNOWN_DATASETS)}"
        )
    
    if not text2sparql_model:
        raise HTTPException(
            status_code=503,
            detail="Model is not available"
        )
    
    try:
        input_text = f"Dataset: {dataset}\nQuestion: {question}"
        generated = text2sparql_model(input_text, max_length=256)
        sparql_query = generated[0]['generated_text']
        
        return {
            "dataset": dataset,
            "question": question,
            "sparql_query": sparql_query,
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating SPARQL: {str(e)}"
        )