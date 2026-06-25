# knowledge/rag.py — Document Q&A using RAG (FAISS + embeddings + Groq).
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import GROQ_API_KEY, MODEL_NAME

_chain = None   # built once, reused (memory-efficient)


def _build_chain():
    """Load docs, embed them, build the FAISS index, and prepare the QA chain. Runs once."""
    from langchain_community.document_loaders import TextLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS

    docs_dir = os.path.join(os.path.dirname(__file__), "docs")
    documents = []
    for fname in os.listdir(docs_dir):
        if fname.endswith(".txt"):
            loader = TextLoader(os.path.join(docs_dir, fname), encoding="utf-8")
            documents.extend(loader.load())

    # split into chunks
    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    chunks = splitter.split_documents(documents)

    # embed + index
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    store = FAISS.from_documents(chunks, embeddings)
    return store


def answer_question(message):
    """Find relevant document chunks and answer using Groq, grounded only in those chunks."""
    global _chain
    if _chain is None:
        _chain = _build_chain()

    # retrieve the most relevant chunks
    results = _chain.similarity_search(message, k=3)
    context = "\n\n".join(r.page_content for r in results)

    if not context.strip():
        return "I couldn't find information about that in the available documents."

    # ask Groq to answer using ONLY the retrieved context
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)
    prompt = (
        "You are a helpful BUITEMS academic assistant. Answer the student's question "
        "using ONLY the information in the context below. If the answer isn't in the context, "
        "say you don't have that information. Keep it clear and short.\n\n"
        f"Context:\n{context}\n\n"
        f"Question: {message}\n\nAnswer:"
    )
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


# quick test
if __name__ == "__main__":
    print(answer_question("What scholarships can I apply for?"))
    print("\n" + "="*50 + "\n")
    print(answer_question("Is there a late fee?"))