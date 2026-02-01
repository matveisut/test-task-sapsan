# DocQA API

REST API для ответов на вопросы по загруженному документу (.docx). Реализовано на FastAPI, LangChain и облачной LLM (OpenRouter).

### Модели

- **LLM:** Arcee AI Trinity Large Preview (через OpenRouter, бесплатно). Ключ — `OPENROUTER_API_KEY` в `.env`.
- **Эмбеддер:** `sentence-transformers/distiluse-base-multilingual-cased-v2` (Hugging Face). Используется для векторного поиска по чанкам документа (русский/английский).

## Требования ТЗ

- Система для ответов на вопросы по документу в Docker-контейнере
- REST на FastAPI: загрузка .docx как контекст, вопросы по документу, ответы в JSON
- LangChain для передачи вопросов в облачную LLM с поддержкой русского языка
- **Три метода API:**
  1. Загрузка файла → возвращает ID файла
  2. Отправка вопроса по файлу → возвращает ID вопроса
  3. Получение ответа по ID вопроса → возвращает ответ или статус обработки (JSON)

## Запуск

```bash
docker compose up --build
```

API будет доступно по адресу: http://localhost:8000

### Переменные окружения

Создайте файл `.env` в корне проекта:

```
OPENROUTER_API_KEY=ваш_ключ
```

Ключ можно получить на https://openrouter.ai (модель Arcee AI Trinity Large Preview — бесплатная).

## Методы API

Все ответы — JSON.

### 1. Загрузка файла (возвращает ID файла)

```http
POST /upload
Content-Type: multipart/form-data
Body: file = <файл .docx>
```

**Ответ:** `{"file_id": "uuid"}`

Пример (curl):
```bash
curl -F "file=@документ.docx" http://localhost:8000/upload
```

### 2. Отправка вопроса по файлу (возвращает ID вопроса)

```http
POST /ask
Content-Type: application/json
Body: {"file_id": "<file_id из шага 1>", "question": "Текст вопроса"}
```

**Ответ:** `{"question_id": "uuid"}`

Пример (curl):
```bash
curl -X POST -H "Content-Type: application/json" -d "{\"file_id\":\"ВАШ_FILE_ID\",\"question\":\"Укажи предмет договора\"}" http://localhost:8000/ask
```

### 3. Получение ответа по ID вопроса (ответ или статус)

```http
GET /result/{question_id}
```

**Ответ:**
- В процессе: `{"status": "pending", "answer": null}`
- Готово: `{"status": "done", "answer": "текст ответа"}`
- Ошибка: `{"status": "error", "error": "описание"}`

Пример (curl):
```bash
curl http://localhost:8000/result/ВАШ_QUESTION_ID
```

Опрос можно повторять, пока `status` не станет `"done"` или `"error"`.
