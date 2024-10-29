import streamlit as st
import json
import re
import pandas as pd
from utils import Utility
from prompt import Prompt
import sqlite3
import os
import logging
from openai import OpenAI
import dashboard

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

# Initialize session state variables at the start
if 'tables_created' not in st.session_state:
    st.session_state.tables_created = False
if 'session_questions' not in st.session_state:
    st.session_state['session_questions'] = []
if 'session_outputs' not in st.session_state:
    st.session_state['session_outputs'] = []
if 'session_figures' not in st.session_state:
    st.session_state['session_figures'] = []
if 'session_response_figures' not in st.session_state:
    st.session_state['session_response_figures'] = []

# Function to handle file uploads and table creation
def handle_file_uploads(uploaded_files, dashboard_name):
    file_paths = [file.name for file in uploaded_files]
    for file in uploaded_files:
        with open(file.name, "wb") as f:
            f.write(file.getbuffer())
    table_names = Utility.create_tables_from_csv(file_paths, dashboard_name)
    st.session_state.tables_created = True
    return table_names

def main():
    st.set_page_config(layout="wide")
    if 'sidebar_state' not in st.session_state:
        st.session_state.sidebar_state = 'expanded'

    if st.button("☰"):
        st.session_state.sidebar_state = 'collapsed' if st.session_state.sidebar_state == 'expanded' else 'expanded'

    if st.session_state.sidebar_state == 'expanded':
        st.sidebar.image("nice_icon.jpeg", width=150)

    st.title("Automated Dashboard and CSV Chatbot")
    dashboard_name = st.text_input("Enter Dashboard Name:")
    uploaded_files = st.file_uploader("Upload CSV Files", accept_multiple_files=True, type="csv")
    api_key = st.text_input("Enter your OpenAI API Key:", type="password")
    dashboard_query = st.text_input("Dashboard topic:")

    if st.button("Generate Dashboard") and dashboard_name and uploaded_files and api_key and dashboard_query:
        if not st.session_state.tables_created:
            table_names = handle_file_uploads(uploaded_files, dashboard_name)
            st.success(f"The tables: {table_names} are created.")

        column_dict = Utility.read_csv_files([file.name for file in uploaded_files])
        sql_prompt, system_prompt = Prompt.get_combined_dashboard_prompt(dashboard_query, column_dict)
        model = Utility.get_openai_creds()  # Only retrieve the model
        response = Responses.get_openai_response(sql_prompt, system_prompt, api_key, model)
        json_content = re.search(r'\{.*?\}', response, re.DOTALL).group(0)
        response_dict = json.loads(json_content)
        df_results_dict = dashboard.get_query_results_dict(response_dict, dashboard_name)
        dashboard.display_graphs_in_grid(df_results_dict, dashboard_name)
        # Save all generated figures in session state
        for df_name, df in df_results_dict.items():
            fig = dashboard.generate_charts(df, df_name)
            if fig:
                st.session_state['session_figures'].append(fig)
                
    
    # CSV Chatbot functionality
    st.markdown("Don't know your data!? Ask us!")
    question = st.text_input("Ask a question:")
    if st.button("Get Response") and question and api_key:
        cols = st.columns(2)  # Create a grid with 2 columns
        for i, fig in enumerate(st.session_state['session_figures']):
            col = cols[i % 2]  # Alternate between the two columns
            with col:
                st.plotly_chart(fig, use_container_width=True, key=f"saved_chart_{i}")
        column_dict = Utility.read_csv_files([file.name for file in uploaded_files])
        sql_prompt, system_prompt = Prompt.get_combined_prompt(question, column_dict)
        model = Utility.get_openai_creds()  # Only retrieve the model
        sql_query = Responses.get_openai_response(sql_prompt, system_prompt, api_key, model)
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        context_df = Responses.execute_query_and_get_result(sql_query, dashboard_name)
        final_prompt = Prompt.get_final_prompt(context_df, question)
        solution = Responses.get_openai_response(prompt=final_prompt, system_prompt=system_prompt, api_key=api_key, model=model)
        if "- **Graph type:** " in solution:
            solution_parts = solution.split("- **Graph type:** ")
            question_answers = solution_parts[0].strip()
            graph_type = solution_parts[1].strip() if len(solution_parts) > 1 else "Not specified"
        else:
            question_answers = solution.strip()
            graph_type = "Not specified"
        # Store question, response, and figure in session state
        st.session_state['session_questions'].append(question)
        st.session_state['session_outputs'].append(question_answers)

        st.write("Response:", question_answers)
        if context_df is not None and not context_df.empty:
            # Determine the name for the context_df based on graph_type and the first column name
            df_name = f"{graph_type}_{context_df.columns[0]}"
            # Generate and display the chart
            fig = dashboard.generate_charts(context_df, df_name)
            if fig:
                # Ensure the figure is displayed in the main response section
                st.plotly_chart(fig, use_container_width=True, key=f"chart_{df_name}")
                # Save the figure in session state
                st.session_state['session_response_figures'].append(fig)
        else:
            st.warning("The context DataFrame is empty or None, unable to generate chart.")
    # Display session history as expandable tiles
    if st.session_state.sidebar_state == 'expanded':
        st.sidebar.header("Chat History")
        for i, (q, a, f) in enumerate(zip(st.session_state['session_questions'], st.session_state['session_outputs'], st.session_state['session_response_figures'])):
            with st.sidebar.expander(f"Q{i+1}: {q}"):
                st.write(f"**A:** {a}")
                st.plotly_chart(f, use_container_width=True, key=f"sidebar_chart_{i}")
    

if __name__ == "__main__":
    main()
