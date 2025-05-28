"""This module contains the main process of the robot."""

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection
from OpenOrchestrator.database.queues import QueueElement
import requests
import json
import pyodbc
from datetime import datetime
import time
import os


# pylint: disable-next=unused-argument
def process(orchestrator_connection: OrchestratorConnection, queue_element: QueueElement | None = None) -> None:
    """Do the primary process of the robot."""
    orchestrator_connection.log_trace("Running process.")
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
            orchestrator_connection.log_info(f"Attempt {attempt} to fetch JSON data...")
            response = requests.get(json_data_source_url)
            response.raise_for_status()
            json_data = response.text
            break
        except requests.exceptions.RequestException as e:
            orchestrator_connection.log_info(f"HTTP request failed (attempt {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                orchestrator_connection.log_info(f"Retrying in {retry_delay_seconds // 60} minutes...")
                time.sleep(retry_delay_seconds)
            else:
                orchestrator_connection.log_info("Max retries reached. Exiting.")
                raise

    # Continue if JSON fetched successfully
    conn = pyodbc.connect(azure_sql_connection_string)
    cursor = conn.cursor()

    json_object = json.loads(json_data)
    rows = json_object.get("rows", [])

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

        # Check if record exists
        cursor.execute("SELECT COUNT(*) FROM Materielopstilling WHERE roadwork_id = ?", roadwork_id)
        existing_row_count = cursor.fetchone()[0]

        if existing_row_count > 0:
            cursor.execute("""
                UPDATE Materielopstilling
                SET changedate = ?, streetname = ?, type_name = ?, startdate = ?, enddate = ?, the_geom = ?
                WHERE roadwork_id = ?
            """, change_date, streetname, type_name, start_date, end_date, the_geom, roadwork_id)
        else:
            cursor.execute("""
                INSERT INTO Materielopstilling
                (roadwork_id, changedate, streetname, type_name, startdate, enddate, the_geom)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, roadwork_id, change_date, streetname, type_name, start_date, end_date, the_geom)

    conn.commit()
    cursor.close()
    conn.close()

