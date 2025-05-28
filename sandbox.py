from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection
import requests
import json
import pyodbc
from datetime import datetime
import time
import os

   
orchestrator_connection = OrchestratorConnection("HenstillingRefresh", os.getenv('OpenOrchestratorSQL'), os.getenv('OpenOrchestratorKey'), None)
sql_credentials = orchestrator_connection.get_credential("AzureSQL")
sql_user = sql_credentials.username
sql_password = sql_credentials.password
sql_server = orchestrator_connection.get_constant("VejmanHistorikSQL").value

json_data_source_url = orchestrator_connection.get_constant("CartoVejman").value
azure_sql_connection_string = (
    f"Driver={{ODBC Driver 17 for SQL Server}};"
    f"Server=tcp:{sql_server};"
    f"Database=TilladelsesHistorik;"
    f"Persist Security Info=False;"
    f"UID={sql_user};"
    f"PWD={sql_password};"
    f"MultipleActiveResultSets=False;"
    f"Encrypt=yes;"
    f"TrustServerCertificate=no;"
    f"Connection Timeout=120;"
)
# Retry settings
max_retries = 3
retry_delay_seconds = 300  # 5 minutes

# Retry HTTP request
for attempt in range(1, max_retries + 1):
    try:
        print(f"Attempt {attempt} to fetch JSON data...")
        response = requests.get(json_data_source_url)
        response.raise_for_status()
        json_data = response.text
        break
    except requests.exceptions.RequestException as e:
        print(f"HTTP request failed (attempt {attempt}/{max_retries}): {e}")
        if attempt < max_retries:
            print(f"Retrying in {retry_delay_seconds // 60} minutes...")
            time.sleep(retry_delay_seconds)
        else:
            print("Max retries reached. Exiting.")
            raise

# Continue if JSON fetched successfully
conn = pyodbc.connect(azure_sql_connection_string)
cursor = conn.cursor()

json_object = json.loads(json_data)
rows = json_object.get("rows", [])
# Define MERGE statement
merge_sql = """
MERGE Materielopstilling AS target
USING (SELECT ? AS roadwork_id, ? AS changedate, ? AS streetname, ? AS type_name, ? AS startdate, ? AS enddate, ? AS the_geom) AS source
ON target.roadwork_id = source.roadwork_id
WHEN MATCHED THEN
    UPDATE SET changedate = source.changedate,
               streetname = source.streetname,
               type_name = source.type_name,
               startdate = source.startdate,
               enddate = source.enddate,
               the_geom = source.the_geom
WHEN NOT MATCHED THEN
    INSERT (roadwork_id, changedate, streetname, type_name, startdate, enddate, the_geom)
    VALUES (source.roadwork_id, source.changedate, source.streetname, source.type_name, source.startdate, source.enddate, source.the_geom);
"""

# Process rows
for item in rows:
    roadwork_id = str(item.get("roadwork_id"))
    change_date = datetime.fromisoformat(item.get("changedate"))
    internal_json_reference = item.get("internal_json_reference_struct")
    type_name = item.get("type_name")
    start_date = datetime.fromisoformat(item.get("startdate"))
    end_date = datetime.fromisoformat(item.get("enddate"))
    the_geom = item.get("the_geom")

    # Extract streetname
    streetname = "Ikke angivet"
    reference_data = json.loads(internal_json_reference)
    if reference_data and isinstance(reference_data, list) and reference_data[0].get("streetname"):
        streetname = reference_data[0]["streetname"]

    # Execute merge
    cursor.execute(
        merge_sql,
        roadwork_id,
        change_date,
        streetname,
        type_name,
        start_date,
        end_date,
        the_geom
    )

# Commit changes
conn.commit()
cursor.close()
conn.close()