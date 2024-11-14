
class Prompt:
    
    @staticmethod
    def get_combined_prompt(question, table_info):
        system_prompt = Prompt.create_system_prompt()
        sql_prompt = Prompt.create_sql_prompt(question, table_info)
        return sql_prompt, system_prompt

    @staticmethod
    def create_system_prompt():
        return "You are an experienced Sql developer with 10 years of experience."

    @staticmethod
    def create_sql_prompt(question, table_info):
        table_names = Prompt.extract_table_names(table_info)
        columns_info = Prompt.format_columns_info(table_info)
        
        return (
            "As a highly advanced SQL query generator, your mission is to craft a precise, efficient, and optimized SQL query. "
            "The query must adhere to standard SQL conventions and be optimized for performance, ensuring it is syntactically correct. "
            "Thoroughly analyze the user's input to ensure the query accurately reflects the intended operations, "
            "including SELECT, INSERT, UPDATE, or DELETE, and incorporates necessary clauses like WHERE, ORDER BY, or GROUP BY. "
            "If some specific mathematical operations are asked in the question, and the columns with that specific values are not available, use sql to correctly perform the mathematical operation and provide the answer."
            "It is essential to correctly integrate table names, column names, and any specified conditions. "
            "Your goal is to produce a query that executes flawlessly in a typical SQL environment, "
            "returning the complete row of data where the conditions are met. "
            "Always use the * in the SELECT statement to retrieve all information unless grouping or counting is required. "
            "Strictly use square brackets for column names to handle cases with spaces. "
            "Select the most appropriate table names from the provided list based on the question, identifying the table with relevant data. "
            "In special cases, understand the necessity to use multiple tables, identifying relationships from the given columns to construct the query. "
            f"<content> User's question: {question} </content>"
            f"The available table names are: {', '.join(table_names)}, strictly use the table names among these. "
            "When grouping or counting is necessary, avoid using * after the SELECT statement. "
            "The data may contain null values; in such cases, do not limit the query to 1, instead, provide the first 5 rows or, if not specifically requested, do not limit the query. "
            "Do not use cases such as top 5 or top. "
            f"<context> {columns_info} </context>"
            "The output should be solely the SQL query, with no additional text or commentary."
        )

    @staticmethod
    def extract_table_names(table_info):
        return list(table_info.keys())

    @staticmethod
    def format_columns_info(table_info):
        return "; ".join([f"Table '{table}' has columns: {', '.join(columns)}" for table, columns in table_info.items()])

    @staticmethod
    def create_final_prompt(result_df, question):
        return f"""
        Based on the given context: {result_df},
        answer the following question: {question}. 
        If the data in context has None, Nan or null values ignore it and give the next most suitable output.
        If the question demands mathematical operations, and the context provided doesn't have the necessary information try to perform the necessary mathematical operation and get the desired answer.
        Do not just read the context data given to you but also provide some actionable insight from the resultant data.
        Plot the given context data frame in a chart by identifying the type of question that is asked, plot a chart in manner which makes most sense.
        Output guidelines: 
        1. The Output should be precise and follow the question given by the user.
        2. The Output should not display the complete df that is provided as context to the llm.
        3. The Output should always be concise and should be informative at the same time.
        4. Understand the user question and based on the data give the answers.
        5. Output should be described in the text format in a sentence or more if required.
        Output Format: 
            Question: {question} \n\n            
            Answer: -> Data-Info : should have numbers and quick overview of the data piece provided in the prompt.
                    -> Key findings : should list the findings from the glance of the data based on the question that is asked.
                    -> Visible trends : should mention and explain any trends that are shown in the data but may be not graspable by mere human eye.
                    -> Actionable Insights : should give a preposition on what needs to be done to enhance, or for betterment of the user with the given insights.
                    -> Graph type : Also provide the graph type for the result_df best possible way to visualize the df:{result_df} the output should be in the form : "bar" in case of bar graphs and "line" in case line graphs and so on, Ensure that output for graph type is one word only. 
        """

    @staticmethod
    def get_final_prompt(result_df, question):
        return Prompt.create_final_prompt(result_df, question)

    @staticmethod
    def create_dashboard_prompt(dashboard_topic, table_info):
        table_names = Prompt.extract_table_names(table_info)
        columns_info = Prompt.format_columns_info(table_info)
        prompt = f"""
Your task is to generate a series of SQL queries based on a provided dataset and a user's key statement. The dataset comprises multiple CSV files, each representing a table. Your objective is to analyze the data according to the user's statement and generate SQL queries suitable for dashboard visualization.

### Reference Data:
- **Table Names**: {table_names}
- **Column Names**: {columns_info}

### Instructions:

#### 1. Data Input:
- You will receive a dataset as described in the reference data.
- The data structure may vary; ensure your approach is adaptable to different datasets.

#### 2. User Statement:
- The user will provide a key statement or guidance, which will be the central focus for your analysis (e.g., "matches").
- Construct a detailed mind map around this key statement, expanding the analysis to encompass all relevant dimensions. For example, if the key statement is "matches," explore areas such as "Wins, losses, successful teams, averages, totals, match types, levels," and more.
- Focus on the most pertinent sections of the dataset, ensuring a targeted and meaningful analysis.

**Example Scenarios**:
- For a key statement like "sales," expand the analysis to include "total revenue, sales growth, top-selling products, regional performance, seasonal trends," etc.
- For "customer feedback," analyze "positive vs. negative feedback, common complaints, customer satisfaction scores, feedback trends over time," and other related aspects.
- With "employee performance," investigate areas like "productivity metrics, performance reviews, training effectiveness, team collaboration," and similar dimensions.

#### 3. Analysis and Insights:
- Conduct a thorough analysis to identify at least 10 compelling insights from the dataset, ensuring they are directly relevant to the user's question.
- Uncover at least 3 notable trends, using a variety of graph types to effectively illustrate these trends.
- Utilize line graphs for time series analysis, bar charts for categorical data comparisons, and scatter plots for examining correlations.
- Incorporate pie charts for proportional data representation and heat maps for visualizing data density or intensity.
- Detect patterns, anomalies, or correlations that could provide valuable insights for decision-making or strategic planning.
- Ensure the insights are diverse, covering multiple facets of the dataset to offer a comprehensive perspective.
- Apply advanced analytical techniques to extract insights that are not immediately apparent, thereby deepening the analysis.
- Clearly articulate the insights and trends in a structured manner that a language model can comprehend, facilitating the generation of meaningful SQL queries for visualization.
- Present the findings in a way that broadens the user's understanding, using visual elements to enhance clarity and engagement.

#### 4. SQL Query Generation:
- Generate precise, efficient, and optimized SQL queries using only the provided table names and their respective column names. Do not invent or assume any additional tables or columns.
- Ensure the queries adhere to standard SQL conventions, maintaining both syntactical and semantic correctness, as well as performance optimization.
- Analyze the user's input to ensure the queries align with the intended operations, such as SELECT, INSERT, UPDATE, or DELETE, and include necessary clauses like WHERE, ORDER BY, or GROUP BY.
- Ensure adherence to the correct SQL syntax and structure when writing queries. Follow these guidelines:
  1. **Clause Order**: Maintain the standard order of SQL clauses. For instance, the `ORDER BY` clause should always follow the `UNION` clause.
  2. **Logical Flow**: Begin with the `SELECT` statement, followed by `FROM`, `WHERE`, `GROUP BY`, `HAVING`, `ORDER BY`, and `LIMIT` as needed.
- Always verify that the SQL query logic aligns with the intended data retrieval and analysis objectives.
- If specific mathematical operations are required and the necessary columns are not available, utilize SQL functions to perform these operations accurately.
- Integrate the provided table names and column names correctly, adhering strictly to the reference data to ensure the queries justify the targeted insights.
- Produce queries that execute flawlessly in a typical SQL environment, accurately displaying the data needed to derive the intended insights.
- Use the * in the SELECT statement to retrieve all columns unless grouping or counting is necessary, ensuring clarity and completeness.
- Use square brackets for column names with spaces to maintain syntactical accuracy.
- Select the most relevant table names from the provided list based on the user's question, ensuring the data source is appropriate for the analysis.
- In cases requiring multiple tables, identify relationships using the given columns to construct coherent queries.
- The available table names are: {', '.join(table_names)}; strictly use these table names.
- When grouping or counting, avoid using * after the SELECT statement to maintain semantic clarity.
- If the data contains null values, do not limit the query to 1. Instead, provide the first 5 rows or, if not specifically requested, do not limit the query.
- Emphasize avoiding constructs like 'SELECT TOP 5' or 'TOP' to prevent syntax errors and ensure the queries remain adaptable and generalizable.
- Adapt to the given context and use meaningful aliases for columns and tables to enhance clarity and user understanding when visualizing data. Ensure aliases are intuitive and reflect the insights or attributes they represent. For example, if the user statement is "Argentina vs Brazil," use aliases like `argentina_goals` and `brazil_goals` to clearly distinguish between the data for each country. Similarly, for a statement like "Q1 vs Q2 Sales," use aliases such as `sales_q1` and `sales_q2`.
- The output should be solely the SQL queries, with no additional text or commentary, ensuring clarity and focus for the LLM.

#### 5. Graph Type Selection:
- Choose the most appropriate graph type based on the nature of the data and the insights you aim to convey. Consider the following guidelines:
  - **Decomposition Tree**: Ideal for breaking down hierarchical data to explore relationships and contributions of different components.
  - **Line Chart**: Best for visualizing trends over time, especially for continuous data.
  - **Bar Chart**: Suitable for comparing quantities across different categories.
  - **Pie Chart**: Useful for showing proportions and percentages within a whole.
  - **Heatmap**: Effective for visualizing data density or intensity across two dimensions.
  - **Column Chart**: Similar to bar charts but oriented vertically, useful for categorical data.
  - **Combo Charts (Line and Bar)**: Combines line and bar charts to compare different data series with distinct scales.
  - **Cards/Tiles for KPIs**: Perfect for displaying key performance indicators in a concise and visually appealing manner.
  - **Funnel Charts**: Ideal for illustrating stages in a process and identifying potential drop-offs.
  - **Gauge Charts**: Useful for showing progress towards a goal or target.
  - **Area Charts**: Good for displaying cumulative totals over time or comparing multiple data series.

#### 6. Output Format:
- Ensure the output contains a minimum of 10 diverse graphs, and mandatorily include between 3 to 4 key performance indicators (KPIs) to provide a comprehensive analysis.
- The output must be a JSON object structured as follows:
  - "dashboard_name": A string representing the name of the dashboard.
  - "graphs": An array of graph objects, each containing:
    - "name": A string for the graph's unique identifier.
    - "type": A string indicating the graph type (e.g., "bar", "line", "pie", "heatmap").
    - "query": A string containing the SQL query for the graph.
    - "x_axis": A string or array indicating the x-axis data.
    - "y_axis": A string or array indicating the y-axis data.
    - "title": A string for the graph's title.
    - "labels": An object mapping data keys to their display labels.
    - "colors": An array of strings indicating the colors to be used for the graph, selected from a professional set of 4-5 colors. Use multiple colors for graphs with multiple labels or fields to distinguish them.

**Example for a Pie Chart**:
"""
        return prompt

    @staticmethod
    def get_combined_dashboard_prompt(dashboard_query, table_info):
        system_prompt = Prompt.create_dashboard_system_prompt()
        sql_prompt = Prompt.create_dashboard_prompt(dashboard_topic=dashboard_query, table_info=table_info)
        return sql_prompt, system_prompt

    @staticmethod
    def create_dashboard_system_prompt():
        return ("You are an expert data analyst with exceptional skills and over 10 years of experience. "
                "Additionally, you are a super expert SQL developer with the same extensive experience. "
                "Your role is to leverage this expertise to analyze data meticulously and generate precise SQL queries. "
                "Focus on delivering insights and solutions that are both innovative and efficient, ensuring clarity and accuracy in all outputs.")