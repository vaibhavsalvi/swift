"""
code_rag_agent.py

A highly organized, agentic Python application that:
- Walks through multiple git projects
- Generates ASTs for source files
- Vectorizes code, AST, and relationships
- Stores embeddings in a vector database
- Uses LangChain and LangGraph for RAG (Retrieval Augmented Generation)
- Answers questions about project domains, code relationships, etc.
- Uses Code2Embed (or similar local embedding model)
- Does NOT use paid OpenAI or paid models

Dependencies: langchain, langgraph, code2embed, chromadb, gitpython, ast, tqdm
"""
import os
import ast
import git
from tqdm import tqdm
from langchain.embeddings import Code2VecEmbeddings  # or Code2Embed if available
from langchain.vectorstores import Chroma
from langchain.schema import Document
from langchain.llms import LlamaCpp  # Example: local LLM
from langgraph.graph import StateGraph, ToolNode

# --- CONFIG ---
VECTOR_DB_DIR = "./vector_db"
EMBEDDING_MODEL_PATH = "./code2embed-model"  # Path to local embedding model
LLM_MODEL_PATH = "./llama-2-7b.Q4_K_M.gguf"  # Path to local LLM

# --- AGENTIC CODE WALKER ---
def walk_git_projects(root_dirs):
    """Yield (project_path, file_path) for all .py files in all git projects under root_dirs."""
    for root_dir in root_dirs:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            if ".git" in dirnames:
                for subdir, _, files in os.walk(dirpath):
                    for file in files:
                        if file.endswith(".py"):
                            yield dirpath, os.path.join(subdir, file)

# --- AST & RELATIONSHIP EXTRACTION ---
def extract_ast_info(file_path):
    """Return AST, relationships, and code for a Python file."""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        code = f.read()
    try:
        tree = ast.parse(code)
    except Exception:
        return None, None, code
    relationships = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                relationships.append(("class_inherits", node.name, getattr(base, 'id', str(base))))
        if isinstance(node, ast.FunctionDef):
            relationships.append(("function", node.name, node.lineno))
    return tree, relationships, code

# --- VECTORIZE & STORE ---
def vectorize_and_store(project, file_path, code, ast_info, relationships, vector_db):
    """Vectorize code, AST, and relationships, and store in vector DB."""
    docs = []
    docs.append(Document(page_content=code, metadata={"project": project, "file": file_path, "type": "code"}))
    if ast_info:
        docs.append(Document(page_content=ast.dump(ast_info), metadata={"project": project, "file": file_path, "type": "ast"}))
    if relationships:
        docs.append(Document(page_content=str(relationships), metadata={"project": project, "file": file_path, "type": "relationships"}))
    vector_db.add_documents(docs)

# --- MAIN PIPELINE ---
def build_vector_db(project_dirs):
    # Use Code2VecEmbeddings or Code2Embed (replace as needed)
    embedder = Code2VecEmbeddings(model_path=EMBEDDING_MODEL_PATH)
    vector_db = Chroma(persist_directory=VECTOR_DB_DIR, embedding_function=embedder)
    for project, file_path in tqdm(list(walk_git_projects(project_dirs)), desc="Indexing projects"):
        ast_info, relationships, code = extract_ast_info(file_path)
        vectorize_and_store(project, file_path, code, ast_info, relationships, vector_db)
    vector_db.persist()
    return vector_db

# --- RAG AGENT ---
def make_rag_agent(vector_db):
    llm = LlamaCpp(model_path=LLM_MODEL_PATH)

    # Tool: Retrieve relevant code/AST/relationships
    def retrieve_tool(query):
        docs = vector_db.similarity_search(query, k=5)
        return docs

    # Tool: Summarize retrieved context
    def summarize_tool(docs):
        context = "\n".join([d.page_content for d in docs])
        return llm(f"Summarize the following code and metadata for high-level understanding.\n{context}\nSummary:")

    # Tool: Answer question using context
    def answer_tool(args):
        docs, question = args
        context = "\n".join([d.page_content for d in docs])
        return llm(f"Context:\n{context}\n\nQuestion: {question}\nAnswer:")

    # StateGraph with multiple nodes and flows
    graph = StateGraph()
    graph.add_node(ToolNode("Retrieve", retrieve_tool))
    graph.add_node(ToolNode("Summarize", summarize_tool))
    graph.add_node(ToolNode("Answer", answer_tool))

    # Define flows: Retrieve -> Summarize, Retrieve -> Answer
    graph.add_edge("Retrieve", "Summarize")
    graph.add_edge("Retrieve", "Answer")

    # Optionally, you can define a start node and a way to run multi-step flows
    graph.set_entry_point("Retrieve")
    return graph

# --- EXAMPLE USAGE ---
if __name__ == "__main__":
    # 1. Index all projects under these directories
    project_dirs = ["./projects"]  # Add your project root(s) here
    vector_db = build_vector_db(project_dirs)

    # 2. Create enhanced agentic RAG agent
    rag_agent = make_rag_agent(vector_db)

    # 3. Ask a question and get retrieval, summary, and answer
    question = "Which domain does the project 'my_project' fall under?"
    # Step 1: Retrieve relevant docs
    docs = rag_agent.run("Retrieve", question)
    # Step 2: Summarize context
    summary = rag_agent.run("Summarize", docs)
    # Step 3: Answer question using context
    answer = rag_agent.run("Answer", (docs, question))
    print("Summary:\n", summary)
    print("Answer:\n", answer)

"""
Notes:
- Replace Code2VecEmbeddings with Code2Embed if available, or another local embedding model.
- LlamaCpp is used for local LLM inference; you can swap for another local LLM supported by LangChain.
- The agentic structure can be extended with more tools, nodes, and memory as needed.
- Relationships and ASTs are stored as documents for semantic linking.
- This is a minimal but highly organized starting point for a codebase RAG agent.
"""
