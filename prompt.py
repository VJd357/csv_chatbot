
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
Your task is to generate a series of SQL queries based on a provided dataset and a user's Key statement. The dataset is composed of multiple CSV files, each representing a table. Your objective is to analyze the data as per the user's statement and create SQL queries that extract data suitable for dashboard visualization.

Reference Data:
- Table Names: {table_names}
- Column Names: {columns_info}

Instructions:

1. **Data Input**: 
   - You will be provided with a dataset described in the reference data.
   - The structure of the data may vary, so your approach should be flexible to accommodate different datasets.

2. **User statement**:
   - The user will provide a Key statement or guidance, indicating the focus area for your analysis (e.g., "matches").
   - Develop a comprehensive mind map around the key statement to broaden the scope of analysis. For instance, if the key statement is "matches," consider analyzing aspects such as "Wins, losses, successful teams, averages, totals, match types, levels," and more. This approach ensures a thorough exploration of the topic.
   - Use this key statement to identify and focus on the most relevant parts of the dataset, ensuring a targeted and insightful analysis.

   **Example Scenarios**:
   - If the user provides a key statement like "sales," expand the analysis to include "total revenue, sales growth, top-selling products, regional performance, seasonal trends," etc.
   - For a key statement such as "customer feedback," consider analyzing "positive vs. negative feedback, common complaints, customer satisfaction scores, feedback trends over time," and other related aspects.
   - With a focus on "employee performance," explore areas like "productivity metrics, performance reviews, training effectiveness, team collaboration," and similar dimensions.

   - These examples illustrate how to open up the area of analysis based on user input, ensuring a comprehensive and insightful exploration of the dataset.

3. **Analysis and Insights**:
   - Conduct a thorough analysis to identify at least 10 compelling insights from the dataset, ensuring they are directly relevant to the user's question.
   - Among these insights, uncover at least 3 notable trends, employing a variety of graph types to effectively illustrate these trends.
   - Utilize line graphs for time series analysis, bar charts for categorical data comparisons, and scatter plots for examining correlations.
   - Additionally, incorporate pie charts for proportional data representation and heat maps for visualizing data density or intensity.
   - Focus on detecting patterns, anomalies, or correlations that could provide valuable insights for decision-making or strategic planning.
   - Ensure the insights are diverse, covering multiple facets of the dataset to offer a comprehensive perspective.
   - Apply advanced analytical techniques to extract insights that are not immediately apparent, thereby deepening the analysis.
   - Clearly articulate the insights and trends in a structured manner that a language model can comprehend, facilitating the generation of meaningful SQL queries for visualization.
   - Present the findings in a way that broadens the user's understanding, using visual elements to enhance clarity and engagement.

4. **SQL Query Generation**:
   - Your task is to generate a precise, efficient, and optimized SQL query using only the provided table names and their respective column names. Do not invent or assume any additional tables or columns.
   - Ensure the query adheres to standard SQL conventions, maintaining both syntactical and semantic correctness, as well as performance optimization.
   - Carefully analyze the user's input to ensure the query aligns with the intended operations, such as SELECT, INSERT, UPDATE, or DELETE, and includes necessary clauses like WHERE, ORDER BY, or GROUP BY.
   - If specific mathematical operations are required and the necessary columns are not available, utilize SQL functions to perform these operations accurately.
   - Integrate the provided table names and column names correctly, adhering strictly to the reference data to ensure the query justifies the targeted insights.
   - Aim to produce a query that executes flawlessly in a typical SQL environment, accurately displaying the data needed to derive the intended insights.
   - Use the * in the SELECT statement to retrieve all columns unless grouping or counting is necessary, ensuring clarity and completeness.
   - Use square brackets for column names with spaces to maintain syntactical accuracy.
   - Select the most relevant table names from the provided list based on the user's question, ensuring the data source is appropriate for the analysis.
   - In cases requiring multiple tables, identify relationships using the given columns to construct a coherent query.
   - The available table names are: {', '.join(table_names)}; strictly use these table names.
   - When grouping or counting, avoid using * after the SELECT statement to maintain semantic clarity.
   - If the data contains null values, do not limit the query to 1. Instead, provide the first 5 rows or, if not specifically requested, do not limit the query.
   - Avoid using constructs like top 5 or top to ensure the query remains adaptable and generalizable.
   - The output should be solely the SQL query, with no additional text or commentary, ensuring clarity and focus for the LLM.

5. **Output Format**:
   - Output should be a JSON object.
   - It is crucial that the keys in the output JSON strictly adhere to the format "chart_type_column_name". This ensures that the keys are both descriptive and consistent, clearly indicating the type of chart and the specific columns involved (e.g., "bar_total_goals"). Adhering to this format is essential for the correct interpretation and generation of SQL queries.
   - Values should be the corresponding SQL queries.
   - Ensure the output is strictly a JSON structure, with no additional statements.

User Input: 
    Instruction: {dashboard_topic}

Example Scenario:
- If the user inquires about "matches", focus on data and insights related to matches among all tables.
- Generate queries to extract data such as total goals, average attendance, and number of matches played.
- Ensure queries can handle both numerical and non-numerical data for a comprehensive dashboard.

The ultimate goal is to create a complete set of SQL queries that can be used to build a dashboard based on the user's question and the provided dataset.
"""
        return prompt

    @staticmethod
    def get_combined_dashboard_prompt(question, table_info):
        system_prompt = Prompt.create_dashboard_system_prompt()
        sql_prompt = Prompt.create_dashboard_prompt(question, table_info)
        return sql_prompt, system_prompt

    @staticmethod
    def create_dashboard_system_prompt():
        return ("You are an expert data analyst with exceptional skills and over 10 years of experience. "
                "Additionally, you are a super expert SQL developer with the same extensive experience. "
                "Your role is to leverage this expertise to analyze data meticulously and generate precise SQL queries. "
                "Focus on delivering insights and solutions that are both innovative and efficient, ensuring clarity and accuracy in all outputs.")