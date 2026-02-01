import io
import uuid
from typing import List, Dict, Any

import docx
from dotenv import load_dotenv
from os import getenv
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings

_STORES: Dict[str, Any] = {}


def load_docx_from_bytes(file_bytes: bytes) -> str:
    bio = io.BytesIO(file_bytes)
    document = docx.Document(bio)
    paragraphs = [p.text.strip() for p in document.paragraphs if p.text and p.text.strip()]
    return "\n\n".join(paragraphs)


def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    splitter = CharacterTextSplitter(
        separator="\n\n",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    return splitter.split_text(text)


def create_vectorstore(chunks: List[str]):
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/distiluse-base-multilingual-cased-v2")
    return FAISS.from_texts(chunks, embeddings)


def create_store_for_document(file_bytes: bytes) -> str:
    text = load_docx_from_bytes(file_bytes)
    chunks = chunk_text(text)
    store = create_vectorstore(chunks)
    doc_id = str(uuid.uuid4())
    _STORES[doc_id] = store
    return doc_id


def get_store(doc_id: str):
    return _STORES.get(doc_id)


def _get_llm():
    load_dotenv()
    api_key = getenv("OPENROUTER_API_KEY")
    if api_key:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            model="arcee-ai/trinity-large-preview:free",
            default_headers={
                "HTTP-Referer": getenv("YOUR_SITE_URL", ""),
                "X-Title": getenv("YOUR_SITE_NAME", ""),
            },
            temperature=0,
        )
    raise RuntimeError("OPENROUTER_API_KEY not found")


def generate_answer(context: str, question: str) -> str:
    llm = _get_llm()
    prompt = (
        "Дан контекст документа (возможны сокращения):\n\n"
        f"{context}\n\n"
        f"Вопрос: {question}\n\n"
        "Дай краткий, точный ответ на русском языке. Если информации недостаточно, честно укажи это."
    )
    resp = llm.invoke(prompt)
    return resp.content if hasattr(resp, "content") else str(resp)


def answer_with_retrieval(doc_id: str, question: str, k: int = 4) -> str:
    store = get_store(doc_id)
    if store is None:
        raise ValueError("Document store not found")
    docs = store.similarity_search(question, k=k)
    context = "\n\n".join([d.page_content for d in docs])
    return generate_answer(context, question)

