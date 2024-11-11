import streamlit as st
import plotly.express as px
import random
import json
import re
import pandas as pd
from utils import Utility
from prompt import Prompt
from main import Responses

def remove_outliers(df, column):
    """Remove outliers from a DataFrame column using the IQR method."""
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]

def create_figure(df, df_name, x_column, y_column):
    """Create a Plotly figure based on the graph type."""
    graph_type = df_name.split('_', 1)[0]
    fig = None
    if graph_type == 'line':
        fig = px.line(df, x=x_column, y=y_column, title=f'{y_column} Trend', markers=True)
    elif graph_type == 'bar':
        fig = px.bar(df, x=x_column, y=y_column, title=f'{y_column} Overview', text=y_column)
        fig.update_xaxes(tickangle=45)
    elif graph_type == 'pie':
        fig = px.pie(df, names=y_column, title=f'{y_column} Breakdown', hole=0.3)
    elif graph_type == 'scatter':
        color_column = df.columns[2] if len(df.columns) > 2 else None
        fig = px.scatter(df, x=x_column, y=y_column, color=color_column, title=f'{y_column} vs {x_column}', size=y_column, hover_data=[x_column])
    elif graph_type == 'box':
        fig = px.box(df, x=x_column, y=y_column, title=f'{y_column} Distribution')
    elif graph_type == 'histogram':
        fig = px.histogram(df, x=y_column, nbins=15, title=f'{y_column} Frequency')
    elif graph_type == 'heatmap':
        fig = px.density_heatmap(df, x=x_column, y=y_column, title=f'{y_column} vs {x_column} Heatmap', color_continuous_scale='Viridis')
    return fig
    

def generate_charts(df, df_name):
    """Generate charts for a given DataFrame and display them."""
    if df is None or df.empty:
        st.warning(f"Skipping {df_name} because the DataFrame is null or empty.")
        return None

    if len(df.columns) == 1 and len(df) == 1:
        column_name = df.columns[0]
        value = df.iloc[0, 0]
        st.markdown(f"<div style='display: inline-block; border: 1px solid #ccc; padding: 10px; text-align: center;'><strong>{column_name} </strong><br><br>{value}</div>", unsafe_allow_html=True)
        return None

    x_column = df.columns[0]
    y_column = df.columns[1]

    if len(df.columns) == 2 and len(df) == 1:
        x_value = df.iloc[0, 0]
        y_value = df.iloc[0, 1]
        st.markdown(f"""
            <div style='display: flex; justify-content: space-between;'>
                <div style='display: inline-block; border: 1px solid #ccc; padding: 10px; text-align: center;'>
                    <h3>{y_column} vs {x_column}</h3>
                    <div style='display: flex; justify-content: space-around;'>
                        <div style='display: flex; flex-direction: column; align-items: center;'>
                            <strong>{x_column} </strong><br><br>
                            <span>{x_value}</span>
                        </div>
                        <div style='display: flex; flex-direction: column; align-items: center;'>
                            <strong>{y_column} </strong><br><br>
                            <span>{y_value}</span>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        return None

    if not pd.api.types.is_numeric_dtype(df[y_column]):
        numerical_columns = df.select_dtypes(include='number').columns
        y_column = numerical_columns[0] if len(numerical_columns) > 0 else None

    if y_column and len(df) > 10:
        df = remove_outliers(df, y_column)

    fig = create_figure(df, df_name, x_column, y_column)
    #if fig:
        #colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        #fig.update_traces(marker_color=random.choice(colors))
    return fig

def get_query_results_dict(response_dict, db_name):
    """Execute queries and return a dictionary of DataFrames."""
    results_dfs = {}
    for name, query in response_dict.items():
        try:
            results_dfs[name] = Responses.execute_query_and_get_result(query, db_name)
        except Exception as e:
            print(f"Skipping query for {name} due to error: {e}")
    return results_dfs

def display_graphs_in_grid(results_dfs, dashboard_name):
    """Display graphs in a grid layout."""
    st.markdown(f'{dashboard_name} Dashboard: ')
    cols = st.columns(2)
    index = 0
    for df_name, df in results_dfs.items():
        try:
            fig = generate_charts(df=df, df_name=df_name)
            if fig:
                with cols[index % 2]:
                    st.plotly_chart(fig)
                index += 1
        except ValueError as e:
            print(f"Skipping {df_name} due to error: {e}")


def main():
    st.set_page_config(layout="wide")
    st.title("Automated Dashboard Generator")
    
    dashboard_name = st.text_input("Enter Dashboard Name:")
    uploaded_files = st.file_uploader("Upload CSV Files", accept_multiple_files=True, type="csv")
    api_key = st.text_input("Enter your OpenAI API Key:", type="password")
    dashboard_query = st.text_input("Dashboard topic:")

    if st.button("Generate Dashboard") and dashboard_name and uploaded_files and api_key and dashboard_query:
        file_paths = [file.name for file in uploaded_files]
        for file in uploaded_files:
            with open(file.name, "wb") as f:
                f.write(file.getbuffer())
        table_names = Utility.create_tables_from_csv(file_paths, dashboard_name)
        st.success(f"The tables: {table_names} are created.")

        column_dict = Utility.read_csv_files(file_paths)
        sql_prompt, system_prompt = Prompt.get_combined_dashboard_prompt(dashboard_query, column_dict)
        model = Utility.get_openai_creds()  # Only retrieve the model
        response = Responses.get_openai_response(sql_prompt, system_prompt, api_key, model)
        json_content = re.search(r'\{.*?\}', response, re.DOTALL).group(0)
        response_dict = json.loads(json_content)
        df_results_dict = get_query_results_dict(response_dict, dashboard_name)
        display_graphs_in_grid(df_results_dict, dashboard_name)

if __name__ == "__main__":
    main()
