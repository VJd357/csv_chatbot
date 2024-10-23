import yaml
import sqlite3
import pandas as pd

class Utility:
    @staticmethod
    def get_openai_creds():
        with open('creds.yaml', 'r') as file:
            creds = yaml.safe_load(file)
        model = creds['openai']['openai_model']
       # api_key = creds['openai']['openai_key']
        return model

    @staticmethod
    def create_tables_from_csv(csv_paths, db_name):
        # Connect to a local SQLite database (or create it if it doesn't exist)
        conn = sqlite3.connect(db_name)
        table_names = []

        for csv_path in csv_paths:
            # Extract table name from the CSV file name
            table_name = csv_path.split('.')[0]
            # Load the CSV file into a DataFrame
            df = pd.read_csv(csv_path)
            # Convert the DataFrame to a SQL table
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            # Append the table name to the list
            table_names.append(table_name)

        # Close the connection
        conn.close()
        return table_names

    @staticmethod
    def read_csv_files(file_paths):
        """
        Iteratively reads CSV files from the given file paths and returns a dictionary:
        A dictionary with table names as keys and lists of column names as values.

        Parameters:
        file_paths (list of str): List of file paths to the CSV files.

        Returns:
        dict: A dictionary with table names as keys and lists of column names as values.
        """
        columns_dict = {}

        for file_path in file_paths:
            df = pd.read_csv(file_path)
            table_name = file_path.split('/')[-1].replace('.csv', '')
            columns_dict[table_name] = df.columns.tolist()

        return columns_dict