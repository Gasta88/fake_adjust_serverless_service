from google.cloud import bigquery
import datetime
import requests
import google.auth.transport.requests
import google.oauth2.id_token
import json
import sys
import time

TABLE_RAW_ID = "justplay-data.analytics_test.adjust_spend_report_by_channel_raw"
TABLE_DAY_ID = "justplay-data.analytics_test.adjust_spend_report_by_channel_day"
ORCHESTRATOR_URL = "https://us-central1-justplay-data.cloudfunctions.net/adjust-api-orchestrator-e2e-test"
EXECUTOR_URL = (
    "https://us-central1-justplay-data.cloudfunctions.net/adjust-api-executor-e2e-test"
)


def set_bq_tables():
    """
    Sets up the BigQuery environment for the given dataset name.

    Returns:
        tuple: A tuple containing the IDs of the raw and day tables.
    """
    client = bigquery.Client(project="justplay-data")
    try:
        client.get_table(TABLE_RAW_ID)
        client.get_table(TABLE_DAY_ID)
    except:
        print("Creating tables")
        schema_raw = [
            bigquery.SchemaField("campaign", "STRING", max_length=500, mode="NULLABLE"),
            bigquery.SchemaField(
                "countryCode", "STRING", max_length=2, mode="NULLABLE"
            ),
            bigquery.SchemaField("osName", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("creative", "STRING", max_length=500, mode="NULLABLE"),
            bigquery.SchemaField("channel", "STRING", max_length=500, mode="NULLABLE"),
            bigquery.SchemaField("installs", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("cost", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("clicks", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("impressions", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("limitAdTrackingInstalls", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("reportDay", "DATE", mode="NULLABLE"),
            bigquery.SchemaField("createdAt", "TIMESTAMP", mode="NULLABLE"),
        ]
        schema_day = [
            bigquery.SchemaField("reportDay", "DATE", mode="NULLABLE"),
            bigquery.SchemaField("updatedAt", "TIMESTAMP", mode="NULLABLE"),
        ]
        # Set expiration date because analytics_test does not have an TTL set
        expiration_time = datetime.datetime.now() + datetime.timedelta(minutes=10)
        table_raw = bigquery.Table(TABLE_RAW_ID, schema=schema_raw)
        table_raw.expires = expiration_time
        table_raw = client.create_table(table_raw)
        table_day = bigquery.Table(TABLE_DAY_ID, schema=schema_day)
        table_day.expires = expiration_time
        table_day = client.create_table(table_day)
    try:
        client.get_table(TABLE_RAW_ID)
        client.get_table(TABLE_DAY_ID)
    except:
        raise RuntimeError("Failed table creation")
    return


def send_post_request():

    request = google.auth.transport.requests.Request()
    token = google.oauth2.id_token.fetch_id_token(request, ORCHESTRATOR_URL)
    data = {"scheduler_id": "2h"}
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(
            ORCHESTRATOR_URL, data=json.dumps(data), headers=headers
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Error: Returned error status code from Adjust, {response.text}"
            )
    except Exception as e:
        raise RuntimeError(e)
    return


def clean_up():
    client = bigquery.Client()
    client.delete_table(TABLE_RAW_ID, not_found_ok=True)
    client.delete_table(TABLE_DAY_ID, not_found_ok=True)
    return


def check_results(table_id):
    client = bigquery.Client()
    while True:
        time.sleep(30)
        query = f"""SELECT COUNT(*) as count FROM `{table_id}`"""
        print("Executing query...")
        result = client.query(query).result().to_dataframe()
        row_count = result.iloc[0, 0]  # Get the count value
        if row_count > 0:
            print(f"Row count for {table_id}: {row_count}")
            break
        else:
            print("Wait for service to complete")
    return


def main():
    print("Starting e2e test")
    set_bq_tables()
    print("Send POST request to orchestrator")
    send_post_request()
    try:
        for table_id in [TABLE_RAW_ID, TABLE_DAY_ID]:
            check_results(table_id)
    except Exception as e:
        print("E2E test failed")
        print("Clean up testing tables")
        clean_up()
        sys.exit(1)
    print("End e2e test")
    return


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error during execution: {e}")
        sys.exit(1)
