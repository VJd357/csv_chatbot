import streamlit as st
from streamlit_chat import message
import tempfile
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import ConversationalRetrievalChain
import openai
import yaml

DB_FAISS_PATH = 'vectorstore/db_faiss'
with open('creds.yaml', 'r') as file:
    creds = yaml.safe_load(file)

model = creds['openai']['openai_model']
api_key = creds['openai']['openai_key']

def load_llm():
    """
    Load the OpenAI language model.

    Returns:
        OpenAI: An instance of the OpenAI model.
    """
    openai.api_key = api_key  # Replace with your actual OpenAI API key
    return openai

def initialize_session_state():
    """
    Initialize session state variables for chat history, generated responses, and past queries.
    """
    if 'history' not in st.session_state:
        st.session_state['history'] = []
    if 'generated' not in st.session_state:
        st.session_state['generated'] = ["Hello, Ask me anything about your uploaded CSV file 🤗"]
    if 'past' not in st.session_state:
        st.session_state['past'] = ["Hey ! 👋"]

def process_uploaded_file(uploaded_file):
    """
    Process the uploaded CSV file and return the data and a retrieval chain.

    Args:
        uploaded_file (UploadedFile): The uploaded CSV file.

    Returns:
        ConversationalRetrievalChain: A retrieval chain for conversational queries.
    """
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name

    loader = CSVLoader(file_path=tmp_file_path, encoding="utf-8", csv_args={'delimiter': ','})
    data = loader.load()

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2", model_kwargs={'device': 'cpu'})
    db = FAISS.from_documents(data, embeddings)
    db.save_local(DB_FAISS_PATH)

    llm = load_llm()
    chain = ConversationalRetrievalChain.from_llm(llm=llm, retriever=db.as_retriever())
    return chain

def conversational_chat(chain, query):
    """
    Get a response from the conversational retrieval chain.

    Args:
        chain (ConversationalRetrievalChain): The retrieval chain.
        query (str): The user's query.

    Returns:
        str: The response from the chain.
    """
    result = chain({'question': query, "chat_history": st.session_state['history']})
    st.session_state['history'].append((query, result["answer"]))
    return result['answer']

def main():
    """
    Main function to run the Streamlit app.
    """
    st.header("Chat with CSV using OpenAI")
    st.markdown("Talk to your CSV Files with Chat CSV Chatbot!")

    uploaded_file = st.sidebar.file_uploader("Upload your CSV file:", type="csv")

    if uploaded_file:
        chain = process_uploaded_file(uploaded_file)
        initialize_session_state()

        user_input = st.chat_input("Chat with your CSV file...")

        if user_input:
            with st.spinner("Generating response..."):
                output = conversational_chat(chain, user_input)
                st.session_state['past'].append(user_input)
                st.session_state['generated'].append(output)

        if st.session_state['generated']:
            for i in range(len(st.session_state['generated'])):
                message(st.session_state['past'][i], is_user=True, key=str(i) + '_user', avatar_style="big-smile")
                message(st.session_state["generated"][i], key=str(i), avatar_style="thumbs")

if __name__ == "__main__":
    main()