import streamlit as st
from openai import OpenAI
from prompt import Prompt
from utils import Utility
import sqlite3
import pandas as pd
import os
import logging

# Configure logging to log.txt
logging.basicConfig(filename='log.txt', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class Responses:
    
    @staticmethod
    def execute_query_and_get_result(query, db_name):
        # Establish connection to the SQLite database
        conn = sqlite3.connect(db_name)
        
        try:
            # Execute the query and load the result into a DataFrame
            result_df = pd.read_sql_query(query, conn)
            # Log the query result
            logging.info(f"Executed Query: {query}\nResult: {result_df.head()}")
        finally:
            # Ensure the connection is closed
            conn.close()
        
        # Return the result
        return result_df

    @staticmethod
    def get_openai_response(prompt, system_prompt, api_key, model):
        client = OpenAI(api_key=api_key)
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
        )
        response_content = completion.choices[0].message.content
        # Log the OpenAI response
        logging.info(f"Prompt: {prompt}\nOpenAI Response: {response_content}")
        return response_content

def main():
    st.sidebar.image("nice_icon.jpeg",  width=150)
    st.title("CSV Chatbot")
    st.markdown("Dont know you data!? Ask us!")
    if 'tables_created' not in st.session_state:
        st.session_state.tables_created = False

    dashboard_name = st.text_input("Enter Dashboard Name:")
    uploaded_files = st.file_uploader("Upload CSV Files", accept_multiple_files=True, type="csv")
    api_key = st.text_input("Enter your OpenAI API Key:", type="password")

    # Check if the database already exists
    if os.path.exists(dashboard_name):
        st.session_state.tables_created = True
        st.success(f"Connected to existing database: {dashboard_name}")

    if st.button("Create Tables") and not st.session_state.tables_created:
        if dashboard_name and uploaded_files:
            file_paths = [file.name for file in uploaded_files]
            for file in uploaded_files:
                with open(file.name, "wb") as f:
                    f.write(file.getbuffer())
            table_names = Utility.create_tables_from_csv(file_paths, dashboard_name)
            st.session_state.tables_created = True
            st.success(f"The tables: {table_names} are created.")
        else:
            st.error("Please provide a dashboard name and upload CSV files.")

    if st.session_state.tables_created:
        question = st.text_input("Ask a question:")
        if st.button("Get Response") and question and api_key:
            if uploaded_files:
                file_paths = [file.name for file in uploaded_files]
            else:
                # Retrieve file paths from the existing database
                conn = sqlite3.connect(dashboard_name)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                table_names = [row[0] for row in cursor.fetchall()]
                file_paths = [f"{name}.csv" for name in table_names]
                conn.close()
            
            column_dict = Utility.read_csv_files(file_paths)
            sql_prompt, system_prompt = Prompt.get_combined_prompt(question, column_dict)
            model = Utility.get_openai_creds()  # Only retrieve the model
            sql_query = Responses.get_openai_response(sql_prompt, system_prompt, api_key, model)
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            context_df = Responses.execute_query_and_get_result(sql_query, dashboard_name)
            final_prompt = Prompt.get_final_prompt(context_df, question)
            solution = Responses.get_openai_response(prompt=final_prompt, system_prompt=system_prompt, api_key=api_key, model=model)
            st.write("Response:", solution)

if __name__ == "__main__":
    main()
