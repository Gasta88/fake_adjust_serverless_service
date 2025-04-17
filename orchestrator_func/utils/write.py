import json
from google.cloud import storage

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

def clean_all_temp_files(bucket_name):
    """
    Deletes all files in the given GCS bucket with the prefix "temp_data".

    Args:
        bucket_name (str): The name of the GCS bucket to delete files from.

    Returns:
        None
    """
    client = storage.Client()
    all_files = [blob for blob in client.list_blobs(bucket_name, prefix="temp_data")]
    for file in all_files:
        file.delete()
    return

