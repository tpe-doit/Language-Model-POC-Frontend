from PyPDF2 import PdfReader
from pathlib import Path
from typing import List, NamedTuple, IO, Tuple
from io import BytesIO
from langchain.text_splitter import RecursiveCharacterTextSplitter  # Text splitting utility
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents.base import Document
from webui_config import EmbeddingModelConfig

MAX_EMBEDDING_BATCH_SIZE = 32 # Hard limit for embedding batch size.

class RagParameters(NamedTuple):
    chunk_size: int
    chunk_overlap: int
    top_k: int
    @classmethod
    def new_rag_parameter(cls, chunk_size, chunk_overlap, top_k=3):
        return cls(chunk_size=chunk_size,
                   chunk_overlap=chunk_overlap, 
                   top_k=top_k)

def load_pdf_to_text(file_like: IO[bytes]) -> List[str]:
    pdf_reader = PdfReader(file_like)
    all_pages = []
    # Get the total number of pages in the PDF
    num_pages = len(pdf_reader.pages)
    for i in range(num_pages):
        page = pdf_reader.pages[i]
        text = page.extract_text()
        all_pages.append(text)
    return all_pages

def split_document(rag_param: RagParameters, document_content: List[str]) -> List[Document]:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=rag_param.chunk_size, chunk_overlap=rag_param.chunk_overlap)
    all_splits = text_splitter.create_documents(document_content)
    return all_splits

def topk_documents(query: str, embedding_config: EmbeddingModelConfig, rag_param: RagParameters, document_path_list:List[str]) -> List[Tuple[Document, float]]:

    if embedding_config.provider.lower() != "huggingface": raise NotImplemented

    # Every elements in 'document_list' is a 'path' to pdf file.
    all_document = []  # Placeholder for all seprated document segments.

    # Load all document.
    for file_path in document_path_list:
        with open(file_path, "rb") as f:
            all_document += split_document(rag_param=rag_param, document_content=load_pdf_to_text(f))

    # Retrive top-k document segments.
    embeddings = HuggingFaceInferenceAPIEmbeddings(
        api_key="",  # type: ignore Dummy API key.
        api_url=embedding_config.endpoint
    )

    # NOTE: Current issue: 'FAISS.from_documents' will STUPIDLY throw all segments of document to embedding model.
    #       So it can cause embedding model dies if batch size is too large.
    #       In the following strategy, first we divide all segment into 'batches' w.r.t. 'MAX_EMBEDDING_BATCH_SIZE'.
    #       Then we create an initial 'vector store', for each batch, we create a temporial 'vector store' and merge to the first one.

    # Divide vector_store w.r.t. the maxium size of batch size (for not exceeding the max batch size of embedding).
    cursor = min(MAX_EMBEDDING_BATCH_SIZE, len(all_document))
    db = FAISS.from_documents(all_document[0:cursor], embeddings) # Initial batch.

    while cursor < len(all_document):
        cursor_next = min(cursor + MAX_EMBEDDING_BATCH_SIZE, len(all_document)) # Calculate next cursoe position.
        _db_temp = FAISS.from_documents(all_document[cursor:cursor_next], embeddings) # Create temp vector store.
        db.merge_from(_db_temp) # Merge vector stores.
        cursor = cursor_next # Move cursor position.
    
    docs_score = db.similarity_search_with_score(query, k=rag_param.top_k)

    return docs_score

