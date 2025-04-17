from .configs import config
import json
from google.cloud import bigquery
from google.cloud import storage
import pandas_gbq


def write_log(main_msg, details=None, severity="INFO"):
    """
    Writes a log message with the given main message, details, and severity level.

    Args:
        main_msg (str): The main message of the log.
        details (str): Additional details to include in the log.
        severity (str): The severity level of the log. Must be one of the following: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'.

    Returns:
        str: A JSON string representing the log message.

    """
    return json.dumps(
        dict(
            severity=severity,
            message=main_msg,
            custom_property=details,
        )
    )


def write_raw_to_bq(df, table_id):
    """
    Writes a pandas DataFrame to a BigQuery table.

    Args:
        df (pandas.DataFrame): The DataFrame to be written to BigQuery.
        table_id (str): The ID of the BigQuery table to write to.

    Raises:
        RuntimeError: If an error occurs while writing to BigQuery.
    """
    try:
        pandas_gbq.to_gbq(
            df, table_id, project_id=config["project_id"], if_exists="append"
        )
    except Exception as e:
        raise RuntimeError(f"Failed data writing: {e}")


def update_day_table(all_files, datetime_now, table_id):
    """
    Updates the updatedAt field in the adjust_spend_report_by_channel_day table in BigQuery with the current datetime.

    Args:
        all_files (list): A list of file names in the GCS temp_data directory.
        datetime_now (str): The current datetime.
        table_id (str): The ID of the table to update.

    Returns:
        None
    """
    client = bigquery.Client()
    start_dates = []
    for file_name in all_files:
        start_date = (
            file_name.split("adjust_report_data_")[1]
            .replace(".csv", "")
            .replace("_", "-")
        )
        start_dates.append(f"{start_date}")
    start_dates = sorted(list(set(start_dates)))
    for start_date in start_dates:
        check_query = f"""SELECT reportDay, updatedAt 
                        FROM {table_id} 
                        WHERE reportDay = '{start_date}'
            """
        rows = client.query(check_query).result()
        if len(list(rows)) == 0:
            query = f"""INSERT INTO {table_id}
                                (reportDay, updatedAt)  
                                VALUES ('{start_date}', '{datetime_now}')
            """
        else:
            query = f"""UPDATE {table_id}
                                SET updatedAt = '{datetime_now}'
                                WHERE reportDay = '{start_date}'
            """
        job = client.query(query)
    return
