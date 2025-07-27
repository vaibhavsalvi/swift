import streamlit as st
from code_rag_agent import build_vector_db, make_rag_agent

st.set_page_config(page_title="Codebase RAG Agent", layout="wide")
st.title("Codebase RAG Agent (LangChain + LangGraph)")


# Sidebar: Project directory selection (with folder picker)
st.sidebar.markdown("### Select your project root folder(s)")
project_dirs = st.sidebar.text_input(
    "Enter project root directories (comma-separated):",
    value="./projects"
)
project_dirs = [d.strip() for d in project_dirs.split(",") if d.strip()]

# Optionally, allow folder upload (for zipped codebases) or single Python file
uploaded_zip = st.sidebar.file_uploader("Or upload a zipped codebase", type=["zip"])
uploaded_py = st.sidebar.file_uploader("Or upload a single Python file", type=["py"])
import zipfile, tempfile, os, shutil
if uploaded_zip is not None:
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    st.sidebar.success(f"Uploaded and extracted to {temp_dir}")
    project_dirs.append(temp_dir)
elif uploaded_py is not None:
    temp_dir = tempfile.mkdtemp()
    py_path = os.path.join(temp_dir, uploaded_py.name)
    with open(py_path, "wb") as f:
        f.write(uploaded_py.read())
    st.sidebar.success(f"Uploaded Python file to {py_path}")
    project_dirs.append(temp_dir)

# Build vector DB and agent (cache for performance)
@st.cache_resource(show_spinner=True)
def get_agent():
    vector_db = build_vector_db(project_dirs)
    rag_agent = make_rag_agent(vector_db)
    return rag_agent

rag_agent = get_agent()

# User query input
query = st.text_area("Ask a question about your codebase:", "Which domain does the project 'my_project' fall under?")

if st.button("Run Agent"):
    with st.spinner("Retrieving relevant code and metadata..."):
        docs = rag_agent.run("Retrieve", query)
    with st.spinner("Summarizing context..."):
        summary = rag_agent.run("Summarize", docs)
    with st.spinner("Generating answer..."):
        answer = rag_agent.run("Answer", (docs, query))
    st.subheader("Summary")
    st.code(summary)
    st.subheader("Answer")
    st.success(answer)
    st.subheader("Retrieved Documents")
    for i, doc in enumerate(docs, 1):
        st.markdown(f"**Doc {i} ({doc.metadata.get('type')})**")
        st.code(doc.page_content[:1000])
