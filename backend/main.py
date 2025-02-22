from fastapi import FastAPI, UploadFile, File
import shutil
import os
import pdfplumber
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# ✅ Load API key from .env file
load_dotenv()
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# ✅ Initialize FastAPI
app = FastAPI()

# ✅ Enable CORS for frontend interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Define request body formats
class QueryRequest(BaseModel):
    user_query: str

# ✅ Create upload directory
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ✅ Load embedding model for retrieval
embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# ✅ Initialize FAISS vector store
index = faiss.IndexFlatL2(384)  # MiniLM has 384-dimensional embeddings
document_store = []  # Store text chunks for retrieval

# ✅ Hugging Face Inference Client
client = InferenceClient(model="tiiuae/falcon-7b-instruct", token=HUGGINGFACE_API_KEY)

# ✅ Function: Extract text from PDF
def extract_text_from_pdf(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + "\n"

        return text.strip() if text else None
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        return None

# ✅ Upload PDF File Endpoint
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    text = extract_text_from_pdf(file_path)
    if text:
        return {"filename": file.filename, "text_preview": text[:500]}
    else:
        return {"filename": file.filename, "text_preview": "No text extracted"}

# ✅ Process PDFs Endpoint
@app.post("/process/")
async def process_pdfs():
    total_chunks = 0

    if not os.listdir(UPLOAD_DIR):  
        return {"error": "No files found to process. Please upload PDFs first!"}

    for file_name in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, file_name)
        text = extract_text_from_pdf(file_path)
        
        if not text:
            continue
        
        chunks = text.split("\n")
        embeddings = embedding_model.encode(chunks, convert_to_numpy=True)

        print(f"📂 Processing {file_name}: {len(chunks)} chunks")  # Debugging print

        index.add(embeddings)
        document_store.extend(chunks)
        total_chunks += len(chunks)

    if total_chunks == 0:
        return {"error": "No valid text found in PDFs. Try another file."}

    return {"message": "PDFs processed successfully", "total_chunks_stored": total_chunks}

# ✅ Function: Retrieve most relevant document chunks
def retrieve_similar_docs(query):
    if index.ntotal == 0:
        return []
    
    query_embedding = embedding_model.encode([query], convert_to_numpy=True)
    _, closest_doc_ids = index.search(query_embedding, k=5)

    return [document_store[i] for i in closest_doc_ids[0] if i < len(document_store)]

# ✅ Query Documents with Hugging Face Model
def retrieve_and_generate_response(query):
    retrieved_docs = retrieve_similar_docs(query)
    if not retrieved_docs:
        return {"response": "No relevant documents found.", "sources": []}

    prompt = f"Use the following excerpts to answer the question:\n{retrieved_docs}\n\nQuery: {query}"
    response = client.text_generation(prompt, max_new_tokens=150)

    return {"response": response, "sources": retrieved_docs}

# ✅ Query Endpoint
@app.post("/query/")
async def query_docs(request: QueryRequest):
    result = retrieve_and_generate_response(request.user_query)
    return {"response": result["response"], "sources": result["sources"]}

#What is the role of the independent registered public accounting firm?