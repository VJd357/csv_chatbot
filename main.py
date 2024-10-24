import streamlit as st
from openai import OpenAI
from prompt import Prompt
from utils import Utility
import sqlite3
import pandas as pd
import os
import logging
from dashboard import generate_profile, generate_visualizations_from_profile

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
    # Add a hamburger menu to toggle the sidebar
    st.set_page_config(layout="wide")
    if 'sidebar_state' not in st.session_state:
        st.session_state.sidebar_state = 'expanded'

    if st.button("☰"):
        st.session_state.sidebar_state = 'collapsed' if st.session_state.sidebar_state == 'expanded' else 'expanded'

    if st.session_state.sidebar_state == 'expanded':
        st.sidebar.image("nice_icon.jpeg", width=150)
        st.sidebar.title("Navigation")
        page = st.sidebar.radio("Go to", ["Home", "Dashboard Generator"])
    else:
        page = st.radio("Go to", ["Home", "Dashboard Generator"], index=0)

    if page == "Home":
        st.title("CSV Chatbot")
        st.markdown("Don't know your data!? Ask us!")

        # Initialize session state variables
        if 'tables_created' not in st.session_state:
            st.session_state.tables_created = False
        if 'session_questions' not in st.session_state:
            st.session_state['session_questions'] = []
        if 'session_outputs' not in st.session_state:
            st.session_state['session_outputs'] = []

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

                # Store question and response in session state
                st.session_state['session_questions'].append(question)
                st.session_state['session_outputs'].append(solution)

                st.write("Response:", solution)

        # Display session history as expandable tiles
        if st.session_state.sidebar_state == 'expanded':
            st.sidebar.header("Chat History")
            for i, (q, a) in enumerate(zip(st.session_state['session_questions'], st.session_state['session_outputs'])):
                with st.sidebar.expander(f"Q{i+1}: {q}"):
                    st.write(f"**A:** {a}")

    elif page == "Dashboard Generator":
        st.title("Automated Dashboard Generator")

        uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])  
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)

            # Generate profile report
            profile = generate_profile(df)

            # Generate visualizations based on profile
            visualizations = generate_visualizations_from_profile(df)

            # Display data overview and visualizations
            if len(visualizations) > 0:
                st.subheader("Data Overview")
                st.write(df.head())

                # Display visualizations in a 3-column layout
                for i in range(0, len(visualizations), 3):
                    cols = st.columns(3)
                    for j, (title, fig) in enumerate(visualizations[i:i+3]):
                        with cols[j]:
                            st.subheader(title)
                            st.plotly_chart(fig, key=f"plot_{i+j}")

if __name__ == "__main__":
    main()
