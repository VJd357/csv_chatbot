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

    # Change the sidebar toggle button to a chat icon
    

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
        # **Important: Append to the list instead of overwriting**
        st.session_state.dashboard_figures.extend(
            [dashboard.generate_charts(df, df_name) for df_name, df in df_results_dict.items() if dashboard.generate_charts(df, df_name)]
        )
        st.session_state.dashboard_name = dashboard_name
        st.session_state.dashboard_query = dashboard_query
        st.session_state.api_key = api_key
        st.session_state.uploaded_files = uploaded_files
        
    # Display the dashboard if it's generated
    if st.session_state.dashboard_name:
        st.header(f"Dashboard: {st.session_state.dashboard_name}")
        cols = st.columns(2)  # Set columns to 2
        for i, fig in enumerate(st.session_state.dashboard_figures):
            with cols[i % 2]:  # Use modulo to cycle through columns
                st.plotly_chart(fig, use_container_width=True, key=f"dashboard_chart_{i}")
    
    # Chatbot UI
    # Only display the chatbot UI if chat_open is True
    st.sidebar.button("💬", key="sidebar_toggle")  # Added unique key
    st.session_state.sidebar_state = 'collapsed' if st.session_state.sidebar_state == 'expanded' else 'expanded'
    if st.session_state.sidebar_state == 'expanded':
        with st.sidebar:
            st.header("Chat with your Data")
            if 'messages' not in st.session_state:
                st.session_state.messages = []
            for i, (q, a) in enumerate(zip(st.session_state['session_questions'], st.session_state['session_outputs'])):
                message(q, is_user=True, key=f"user_{i}")
                message(a, is_user=False, key=f"bot_{i}")
            # Fix the input box and send button position
            #st.markdown(
            #    """
            #    <style>
            #    .sidebar-content {
            #        position: fixed;
            #        top: 0;
            #        width: 100%;
            #    }
            #    .sidebar-content > * {
            #        margin-bottom: 10px;
            #    }
            #    .sidebar-content input[type="text"] {
            #        width: 100%;
            #        padding: 10px;
            #        border: 1px solid #ccc;
            #        border-radius: 5px;
            #        box-sizing: border-box;
            #    }
            #    .sidebar-content button {
            #        width: 100%;
            #        padding: 10px;
            #        background-color: #4CAF50;
            #        color: white;
            #        border: none;
            #        border-radius: 5px;
            #        cursor: pointer;
            #    }
            #    </style>
            #    """,
            #    unsafe_allow_html=True
            #)
            #st.markdown("<div class='sidebar-content'>", unsafe_allow_html=True)
            question = st.text_input("Ask a question:", key="question_input")
            if st.button("Send", key="send_question"):
                  # Added unique key
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
            #st.markdown("</div>", unsafe_allow_html=True)
    # Display session history as expandable tiles
    #if st.session_state.sidebar_state == 'expanded':
    #    st.sidebar.header("Chat History")
    #    for i, (q, a, f) in enumerate(zip(st.session_state['session_questions'], st.session_state['session_outputs'], st.session_state['session_response_figures'])):
    #        with st.sidebar.expander(f"Q{i+1}: {q}"):
    #            st.write(f"**A:** {a}")
    #            st.plotly_chart(f, use_container_width=True, key=f"sidebar_chart_{i}")
    
    # Add JavaScript to scroll to the bottom of the sidebar
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
    

if __name__ == "__main__":
    main()
