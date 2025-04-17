from .configs import config
from .write import write_log
import requests
import pandas as pd
import time
from google.cloud import storage


def get_bq_dataset(function_name):
    """
    Retrieves the BigQuery dataset name based on the provided function name.

    Args:
        function_name (str): The name of the function to determine the dataset for.

    Returns:
        str: The name of the BigQuery dataset.

    Raises:
        ValueError: If the function name does not contain 'dev' or 'prod'.
    """
    if function_name.split("-")[-1] in ["dev", "bulk", "test"]:
        return "analytics_test"
    elif "prod" in function_name:
        return "analytics"
    else:
        raise ValueError("Unable to infer DEV or PROD from function name")


def get_with_url(url, api_key=""):
    """
    Fetches data from a specified URL using an Adjust API key and returns the data as a list of rows.

    Args:
        url (str): The URL to fetch data from.
        api_key (str, optional): The Adjust API key to use for authentication. Defaults to an empty string.

    Returns:
        list: A list of rows containing the fetched data.

    Raises:
        RuntimeError: If the request returns a status code other than 200 or if an exception occurs during the request.
    """
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        response = requests.get(
            url, headers=headers, timeout=config["timeout_limit_seconds"]
        )
        response.raise_for_status()
        return response.json().get("rows", [])
    except requests.exceptions.HTTPError as http_err:
        print(
            write_log(
                f"HTTP error occurred: {http_err}",
                details=response.text,
                severity="WARNING",
            )
        )
    except requests.exceptions.Timeout:
        print(write_log("Executor timeout", severity="WARNING"))
    except requests.exceptions.RequestException as req_err:
        print(write_log(f"Request exception occurred: {req_err}", severity="WARNING"))
    return []


def _to_camel_case(snake_str):
    """
    Converts a snake_case string to camelCase.

    Args:
        snake_str (str): The snake_case string to convert.

    Returns:
        str: The converted camelCase string.

    Example:
        >>> _to_camel_case("snake_case_string")
        'snakeCaseString'
    """
    camel_string = "".join(x.capitalize() for x in snake_str.lower().split("_"))
    return snake_str[0].lower() + camel_string[1:]


def clean_raw_data(data, datetime_now):
    """
    Cleans and processes raw data from the input source.

    Args:
        data: The raw data to be cleaned and processed.
        datetime_now (str): The current datetime.

    Returns:
        pandas DataFrame: The cleaned and processed raw data with added reportDay and createdAt columns.
    """
    df_raw = pd.DataFrame(data)
    df_raw = df_raw.astype({col: "int64" for col in config["integer_cols"]})
    df_raw = df_raw.astype({col: "float64" for col in config["float_cols"]})
    df_raw.columns = [_to_camel_case(col) for col in df_raw.columns]
    df_raw.rename(columns={"day": "reportDay"}, inplace=True)
    df_raw["createdAt"] = pd.to_datetime(datetime_now)
    df_raw = df_raw[config["ordered_columns"]]
    return df_raw


def get_bq_tables(dataset_name):
    """
    Gets the BigQuery environment for the given dataset name and function name.

    Args:
        function_name (str): The name of the function being executed.
        dataset_name (str): The name of the dataset to set up.

    Returns:
        tuple: A tuple containing the IDs of the raw and day tables.
    """
    table_raw_id = f"{config['project_id']}.{dataset_name}.{config['table_raw_name']}"
    table_day_id = f"{config['project_id']}.{dataset_name}.{config['table_day_name']}"
    return (table_raw_id, table_day_id)


def get_temp_prefix(bucket_name, start_date, platform):
    """
    Generate a GCS file name for temporary storage of raw data.

    Args:
        bucket_name (str): The name of the GCS bucket to store the file in.
        start_date (str): The date of the data being stored, in YYYY-MM-DD format.
        platform (str): The platform of the data (ios or android).

    Returns:
        str: The GCS file name.
    """
    return f'{bucket_name}/temp_data/{platform}/adjust_report_data_{start_date.replace("-","_")}.csv'


def get_all_temp_files(bucket_name, scheduler_id):
    """
    Retrieve all temporary files from GCS, waiting until all files are present.

    Args:
        bucket_name (str): The name of the GCS bucket to retrieve files from.
        scheduler_id (str): The ID of the scheduler that generated the files ("7d" or "1m").

    Returns:
        list: A list of all temporary file names.
    """
    client = storage.Client()
    if scheduler_id == "2h":
        # the 2h Scheduler should generate 5 (days) * 2 (platforms) files
        expected_num_files = 10
    if scheduler_id == "7d":
        # the 7d Scheduler should generate 14 (days) * 2 (platforms) files
        expected_num_files = 28
    if scheduler_id == "1m":
        # the 1m Scheduler should generate 30 (days) * 2 (platforms) files
        expected_num_files = 60
    while True:
        all_files = [
            f"{bucket_name}/{blob.name}"
            for blob in client.list_blobs(bucket_name, prefix="temp_data")
        ]
        print(
            write_log(
                f"Expected {expected_num_files} files, found {len(all_files)} files in GCS bucket"
            )
        )
        if len(all_files) == expected_num_files:
            break
        time.sleep(30)
    return all_files


def get_temp_df(all_files):
    """
    Reads all temporary files stored in GCS and concatenates them into a single DataFrame.

    Args:
        all_files (list): A list of the names of all files in the GCS bucket with the prefix "temp_data".

    Returns:
        pandas DataFrame: The concatenated DataFrame containing all data from the temporary files.
    """
    dfs = []
    for temp_file in all_files:
        dfs.append(pd.read_csv(f"gs://{temp_file}"))
    df_raw = pd.concat(dfs)
    df_raw["createdAt"] = pd.to_datetime(df_raw["createdAt"])
    return df_raw
