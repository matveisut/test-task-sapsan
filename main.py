from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from pydantic import BaseModel
import tempfile
import uuid
import os
from typing import Dict, Any

import rag_service

app = FastAPI(title="DocQA API", version="0.1.0")

# Хранилище в памяти: file_id -> путь к сохранённому .docx
uploaded_files: Dict[str, str] = {}
# Статусы вопросов: question_id -> {"status": "pending"|"done"|"error", "answer": ... или "error": ...}
questions_status: Dict[str, Dict[str, Any]] = {}


class AskRequest(BaseModel):
    file_id: str
    question: str


@app.get("/")
async def root():
    return {"message": "DocQA API"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Загрузка .docx во временную папку, возвращает file_id."""
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported")

    contents = await file.read()
    file_id = str(uuid.uuid4())
    path = os.path.join(tempfile.gettempdir(), f"{file_id}.docx")
    with open(path, "wb") as f:
        f.write(contents)

    uploaded_files[file_id] = path
    return {"file_id": file_id}


def _process_question_task(question_id: str, file_id: str, question: str):
    """Фоновая задача: строит векторное хранилище по файлу, получает ответ через RAG, пишет в questions_status."""
    try:
        if file_id not in uploaded_files:
            questions_status[question_id] = {"status": "error", "error": "file_id not found"}
            return

        with open(uploaded_files[file_id], "rb") as f:
            file_bytes = f.read()

        doc_store_id = rag_service.create_store_for_document(file_bytes)
        answer = rag_service.answer_with_retrieval(doc_store_id, question)
        questions_status[question_id] = {"status": "done", "answer": answer}
    except Exception as e:
        questions_status[question_id] = {"status": "error", "error": str(e)}


@app.post("/ask")
async def ask_question(payload: AskRequest, background_tasks: BackgroundTasks):
    """Принимает file_id и question, запускает обработку в фоне, сразу возвращает question_id."""
    if payload.file_id not in uploaded_files:
        raise HTTPException(status_code=404, detail="file_id not found")

    question_id = str(uuid.uuid4())
    questions_status[question_id] = {"status": "pending", "answer": None}
    background_tasks.add_task(_process_question_task, question_id, payload.file_id, payload.question)
    return {"question_id": question_id}


@app.get("/result/{question_id}")
async def get_result(question_id: str):
    """Возвращает статус обработки и ответ (если готов) или ошибку."""
    if question_id not in questions_status:
        raise HTTPException(status_code=404, detail="question_id not found")
    return questions_status[question_id]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
