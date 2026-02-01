# DocQA API

REST API для ответов на вопросы по загруженному документу (.docx). Реализовано на FastAPI, LangChain и облачной LLM (OpenRouter).

## Требования ТЗ — соблюдены

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

## Сценарий для видео (тестовое задание)

1. **Получить документ в формате .docx**  
   По ссылке из ТЗ (Google Docs) откройте документ → Файл → Скачать → Microsoft Word (.docx). Сохраните файл на компьютер.

2. **Запустить API:**  
   `docker compose up --build`

3. **Загрузить документ** (в ответе будет `file_id`):
   ```bash
   curl -F "file=@путь/к/документу.docx" http://localhost:8000/upload
   ```

4. **Задать четыре вопроса** (подставьте полученный `file_id`; после каждого запроса сохраняйте `question_id` из ответа):

   - Укажи предмет договора  
     `curl -X POST -H "Content-Type: application/json" -d "{\"file_id\":\"FILE_ID\",\"question\":\"Укажи предмет договора\"}" http://localhost:8000/ask`

   - Какой номер и дата у этого договора?  
     `curl -X POST -H "Content-Type: application/json" -d "{\"file_id\":\"FILE_ID\",\"question\":\"Какой номер и дата у этого договора?\"}" http://localhost:8000/ask`

   - Какие штрафные санкции предусматривает этот договор в отношении поставщика?  
     `curl -X POST -H "Content-Type: application/json" -d "{\"file_id\":\"FILE_ID\",\"question\":\"Какие штрафные санкции предусматривает этот договор в отношении поставщика?\"}" http://localhost:8000/ask`

   - Какие штрафные санкции предусматривает этот договор в отношении покупателя?  
     `curl -X POST -H "Content-Type: application/json" -d "{\"file_id\":\"FILE_ID\",\"question\":\"Какие штрафные санкции предусматривает этот договор в отношении покупателя?\"}" http://localhost:8000/ask`

5. **Получить ответы** — для каждого `question_id` вызвать:
   ```bash
   curl http://localhost:8000/result/QUESTION_ID
   ```
   Повторять запрос, пока в ответе не будет `"status": "done"` и поле `"answer"` с текстом.
