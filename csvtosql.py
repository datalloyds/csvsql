import streamlit as st
import pandas as pd
import pyodbc

st.set_page_config(page_title="CSV to SQL Server Loader", layout="centered")

st.title("📥 CSV to SQL Server Table Loader")

# Upload CSV
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if uploaded_file:
    # Load CSV with quote handling
    df = pd.read_csv(uploaded_file, quotechar='"')
    df = df.applymap(lambda x: x.strip('"') if isinstance(x, str) else x)

    st.success("CSV loaded successfully and cleaned!")
    st.dataframe(df.head())

    # SQL Connection Details
    st.header("🔐 SQL Server Connection")
    server = st.text_input("Server", value="localhost")
    database = st.text_input("Database")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    table_name = st.text_input("Target Table Name")

    if st.button("🚀 Upload to SQL Server"):
        try:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};DATABASE={database};UID={username};PWD={password}"
            )
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()

            # Remove identity column if present
            identity_col = "CatCodeID"
            insert_df = df.copy()
            if identity_col in insert_df.columns:
                insert_df = insert_df.drop(columns=[identity_col])
                st.warning(f"Auto-increment identity column `{identity_col}` excluded from insert.")

            # Create table if not exists
            col_defs = ", ".join([f"[{col}] NVARCHAR(MAX)" for col in insert_df.columns])
            create_sql = f"""
                IF OBJECT_ID('{table_name}', 'U') IS NULL 
                CREATE TABLE {table_name} ({col_defs})
            """
            cursor.execute(create_sql)

            # Insert data
            for _, row in insert_df.iterrows():
                values = [str(val).replace("'", "''") for val in row]
                column_list = ", ".join(f"[{col}]" for col in insert_df.columns)
                value_list = "', '".join(values)
                sql = f"INSERT INTO {table_name} ({column_list}) VALUES ('{value_list}')"
                cursor.execute(sql)

            conn.commit()
            cursor.close()
            conn.close()

            st.success(f"✅ Data successfully inserted into `{table_name}`!")

        except Exception as e:
            st.error(f"❌ Error: {e}")
