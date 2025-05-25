from __future__ import annotations
import json, os
from pathlib import Path
import numpy as np
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain
from langserve import add_routes
from langchain.schema.runnable import Runnable

# -----------------------------------------------------------------------------
# Config utils
# -----------------------------------------------------------------------------
def load_config() -> dict:
    cfg_path = os.getenv("CONFIG_PATH") or Path(__file__).parent / "config.json"
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)

ENV_PATH = Path(__file__).parent / ".env"
if ENV_PATH.is_file():
    load_dotenv(ENV_PATH)

config = load_config()

# -----------------------------------------------------------------------------
# Pre-compute embeddings for allow-list
# -----------------------------------------------------------------------------
embeddings = OpenAIEmbeddings()
allowed_texts = list(config["canonical_allowed"].keys())
allowed_vectors = np.array(embeddings.embed_documents(allowed_texts))

THRESHOLD = config["threshold"]

def most_similar_allowed(question: str) -> str | None:
    q_vec = np.array(embeddings.embed_query(question))
    sims = allowed_vectors @ q_vec / (
        np.linalg.norm(allowed_vectors, axis=1) * np.linalg.norm(q_vec)
    )
    idx = int(np.argmax(sims))
    return allowed_texts[idx] if sims[idx] >= THRESHOLD else None

# -----------------------------------------------------------------------------
# Build LangChain runnable
# -----------------------------------------------------------------------------
def build_chain():
    vectordb = Chroma(
        persist_directory="db",
        embedding_function=embeddings,
    )

    rag_chain = ConversationalRetrievalChain.from_llm(
        llm=ChatOpenAI(
            model=config["llm"]["model"],
            temperature=config["llm"]["temperature"],
        ),
        retriever=vectordb.as_retriever(
            search_type=config["retriever"]["search_type"],
            k=config["retriever"]["k"],
        ),
    )

    config_root = config

    class Allowlist(Runnable):
        def invoke(self, inputs, config=None):
            question = inputs["question"].strip().lower()
            if not most_similar_allowed(question):
                return {"answer": config_root["refusal_text"]}
            return rag_chain.invoke(
                {
                    "question": question,
                    "chat_history": inputs.get("chat_history", []),
                },
                config=config,
            )

    return Allowlist()

# -----------------------------------------------------------------------------
# FastAPI app & routes
# -----------------------------------------------------------------------------
app = FastAPI(**config["fastapi"])

add_routes(app, build_chain(), path="/chat")

FRONTEND_DIR = Path(__file__).parent.parent / "ui"
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
