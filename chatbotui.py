import streamlit as st
from langchain.llms import OpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

st.title("Chatbot UI")

llm = OpenAI(temperature=0.7)
memory = ConversationBufferMemory()
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True,
)

st.header("Chat with me!")

user_input = st.text_input("Enter your message:")

if user_input:
    response = conversation.run(user_input)
    st.write(f"**Bot:** {response}")
