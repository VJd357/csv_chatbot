
class Prompt:
    
    @staticmethod
    def get_combined_prompt(question, table_info):
        system_prompt = Prompt.create_system_prompt()
        sql_prompt = Prompt.create_sql_prompt(question, table_info)
        return system_prompt, sql_prompt

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
            "The data may contain null values; in such cases, do not limit the query to 1. Instead, provide the first 5 rows or, if not specifically requested, do not limit the query. "
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
        Output guidelines: 
        1. The Output should be precise and follow the question given by the user.
        2. The Output should not display the complete df that is provided as context to the llm.
        3. The Output should always be concise and should be informative at the same time.
        4. Understand the user question and based on the data give the answers.
        5. Output should be described in the text format in a sentence or more if required.
        Output Format: 
            Question: {question} \n\n            
            Answer: response
        
        """

    @staticmethod
    def get_final_prompt(result_df, question):
        return Prompt.create_final_prompt(result_df, question)

