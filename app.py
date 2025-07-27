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


# Build vector DB and agent only after user clicks 'Build Index'
if 'rag_agent' not in st.session_state:
    st.session_state['rag_agent'] = None
    st.session_state['rag_app'] = None
    st.session_state['vector_db_ready'] = False

if st.button("Build Index"):
    with st.spinner("Building vector database and agent..."):
        vector_db = build_vector_db(project_dirs)
        rag_agent = make_rag_agent(vector_db)
        rag_app = rag_agent.compile()
        st.session_state['rag_agent'] = rag_agent
        st.session_state['rag_app'] = rag_app
        st.session_state['vector_db_ready'] = True

rag_app = st.session_state.get('rag_app', None)

# User query input
query = st.text_area("Ask a question about your codebase:", "Which domain does the project 'my_project' fall under?")

if rag_app and st.session_state['vector_db_ready']:
    if st.button("Run Agent"):
        with st.spinner("Retrieving relevant code and metadata..."):
            docs = rag_app.invoke({"input": query, "node": "Retrieve"})
        with st.spinner("Summarizing context..."):
            summary = rag_app.invoke({"input": docs, "node": "Summarize"})
        with st.spinner("Generating answer..."):
            answer = rag_app.invoke({"input": (docs, query), "node": "Answer"})
        st.subheader("Summary")
        st.code(summary)
        st.subheader("Answer")
        st.success(answer)
        st.subheader("Retrieved Documents")
        for i, doc in enumerate(docs, 1):
            st.markdown(f"**Doc {i} ({doc.metadata.get('type')})**")
            st.code(doc.page_content[:1000])
else:
    st.info("Please upload your code and click 'Build Index' before running the agent.")
