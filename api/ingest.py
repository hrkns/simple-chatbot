from pathlib import Path
import json, os, pathlib
from dotenv import load_dotenv

from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.docstore.document import Document

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
# Ingestion
# -----------------------------------------------------------------------------
def main() -> None:
    loader = WebBaseLoader(
        config["source_urls"],
        requests_kwargs={"timeout": tuple(config["loader_timeout"])},
    )
    docs = loader.load()

    # Optional extra docs
    extra = [
        Document(**doc) for doc in config.get("extra_documents", [])
    ]
    docs.extend(extra)

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)
    splits = splitter.split_documents(docs)

    vectordb = Chroma.from_documents(
        documents=splits,
        embedding=OpenAIEmbeddings(),
        persist_directory="db",
    )
    vectordb.persist()
    print("✅ Vector DB built at ./db")

# -----------------------------------------------------------------------------
if __name__ == "__main__":
    assert os.getenv("OPENAI_API_KEY"), "Set OPENAI_API_KEY first!"
    pathlib.Path("db").mkdir(exist_ok=True)
    main()
