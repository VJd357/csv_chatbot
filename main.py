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
from streamlit_chat import message
from dashboard_visualization import GraphPlotter

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


# Function to handle file uploads and table creation
def handle_file_uploads(uploaded_files, dashboard_name):
    file_paths = [file.name for file in uploaded_files]
    for file in uploaded_files:
        with open(file.name, "wb") as f:
            f.write(file.getbuffer())
    table_names = Utility.create_tables_from_csv(file_paths, dashboard_name)
    st.session_state.tables_created = True
    return table_names


def enrich_graphs_with_data(response_dict, dashboard_name):
    """Enrich each graph in the response_dict with data from the executed query and return the updated dictionary."""
    for graph in response_dict.get('graphs', []):
        query = graph.get('query')
        if query:
            try:
                # Execute the query and get the result
                result_df = Responses.execute_query_and_get_result(query, dashboard_name)
                # Append the result to the graph dict under the key 'data'
                graph['data'] = result_df
            except Exception as e:
                # Print the query that caused an error
                print(f"Error executing query: {query}\nException: {e}")
    return response_dict

def main():
    st.set_page_config(layout="wide")
    
    # Initialize session state variables at the start
    if 'sidebar_state' not in st.session_state:
        st.session_state.sidebar_state = 'collapsed'
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
    if 'dashboard_name' not in st.session_state:
        st.session_state.dashboard_name = None
    if 'dashboard_figures' not in st.session_state:
        st.session_state.dashboard_figures = []
    if 'dashboard_query' not in st.session_state:
        st.session_state.dashboard_query = None
    if 'api_key' not in st.session_state:
        st.session_state.api_key = None
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = []

    st.title("ConverSight")
    dashboard_name = st.text_input("Enter Database Name:")
    uploaded_files = st.file_uploader("Upload CSV Files", accept_multiple_files=True, type="csv")
    api_key = st.text_input("Enter your OpenAI API Key:", type="password")
    dashboard_query = st.text_input("Dashboard topic:")

    if st.button("Generate Dashboard") and dashboard_name and uploaded_files and api_key and dashboard_query:
        if not st.session_state.tables_created:
            table_names = handle_file_uploads(uploaded_files, dashboard_name)
            st.success(f"The tables: {table_names} are created.")
            st.session_state.tables_created = True

        column_dict = Utility.read_csv_files([file.name for file in uploaded_files])
        sql_prompt, system_prompt = Prompt.get_combined_dashboard_prompt(dashboard_query, column_dict)
        model = Utility.get_openai_creds()  # Only retrieve the model
        response = Responses.get_openai_response(sql_prompt, system_prompt, api_key, model)
        cleaned_json = Utility.clean_markdown(response)
        response_dict = json.loads(cleaned_json)
        data_dict = enrich_graphs_with_data(response_dict, dashboard_name)
        
        # Use GraphPlotter to plot graphs in grid
        plotter = GraphPlotter(data_dict)
        plotter.plot_graphs_in_grid()
        
        # Store dashboard-related session state
        st.session_state.dashboard_name = data_dict.get('dashboard_name', dashboard_name)
        st.session_state.dashboard_query = dashboard_query
        st.session_state.api_key = api_key
        st.session_state.uploaded_files = uploaded_files
        st.session_state.dashboard_figures = plotter.get_figures()  # Store the figures

    # Chatbot UI
    st.sidebar.button("💬", key="sidebar_toggle")  # Added unique key
    st.session_state.sidebar_state = 'collapsed' if st.session_state.sidebar_state == 'expanded' else 'expanded'
    if st.session_state.sidebar_state == 'expanded':
        with st.sidebar:
            st.header("Chat with your Data")
            if 'messages' not in st.session_state:
                st.session_state.messages = []

            # Recreate the database when the sidebar is expanded
            if st.session_state.uploaded_files and st.session_state.dashboard_name:
                table_names = handle_file_uploads(st.session_state.uploaded_files, st.session_state.dashboard_name)
                st.success(f"The tables: {table_names} are recreated for the chatbot.")
            else:
                st.error("Dashboard name or uploaded files are missing.")

            for i, (q, a) in enumerate(zip(st.session_state['session_questions'], st.session_state['session_outputs'])):
                message(q, is_user=True, key=f"user_{i}")
                message(a, is_user=False, key=f"bot_{i}")
            question = st.text_input("Ask a question:", key="question_input")
            if st.button("Send", key="send_question"):
                column_dict = Utility.read_csv_files([file.name for file in st.session_state.uploaded_files])
                sql_prompt, system_prompt = Prompt.get_combined_prompt(question, column_dict)
                model = Utility.get_openai_creds()  # Only retrieve the model
                sql_query = Responses.get_openai_response(sql_prompt, system_prompt, st.session_state.api_key, model)
                sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
                context_df = Responses.execute_query_and_get_result(sql_query, st.session_state.dashboard_name)
                final_prompt = Prompt.get_final_prompt(context_df, question)
                solution = Responses.get_openai_response(prompt=final_prompt, system_prompt=system_prompt, api_key=st.session_state.api_key, model=model)
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
                    print("The context DataFrame is empty or None, unable to generate chart.")
        st.sidebar.markdown(
        """
        <style>
        .stSidebar > div {
            overflow-y: auto;
            height: calc(100vh - 60px); /* Adjust height as needed */
        }
        </style>
        """,
        unsafe_allow_html=True
        )

    # Display the most recent dashboard if it's generated
    if st.session_state.dashboard_name and st.session_state.dashboard_figures:
        st.header(f"Dashboard: {st.session_state.dashboard_name}")
        cols = st.columns(2)  # Set columns to 2
        for i, fig in enumerate(st.session_state.dashboard_figures):
            if fig:  # Ensure the figure is not None
                with cols[i % 2]:  # Use modulo to cycle through columns
                    st.plotly_chart(fig, use_container_width=True, key=f"dashboard_chart_{i}")

if __name__ == "__main__":
    main()