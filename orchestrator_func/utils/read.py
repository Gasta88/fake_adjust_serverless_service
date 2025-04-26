from .configs import config
from .write import write_log
from google.cloud import storage
import google.auth.transport.requests
import google.oauth2.id_token
import json
import datetime
import time
import requests


def _post_with_url(url, data={}):
    """
    Post data to a URL with GCP service account authentication.

    Args:
        url (str): The URL to POST to.
        data (dict): The data to send in the POST request.

    Notes:
        - The function uses the `fetch_id_token` method from the `google.auth.transport.requests` module to
          authenticate the request with the service account.
        - The function sets the `Authorization` and `Content-Type` headers to `Bearer <token>` and
          `application/json`, respectively.
        - The function attempts to POST the data with a very short timeout (5 seconds) to emulate a
          fire-and-forget mechanism. If a `ReadTimeout` exception is raised, it is caught and ignored.
    """
    request = google.auth.transport.requests.Request()
    token = google.oauth2.id_token.fetch_id_token(request, url)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    print(write_log(f'Sending POST request for {data["start_date"]}', f"Data: {data}"))
    try:
        # use a very short timeout for a hacky fire-and-forget mechanism
        response = requests.post(url, data=json.dumps(data), headers=headers, timeout=5)
    except requests.exceptions.ReadTimeout:
        pass
    return


def _get_date_periods(scheduler_id):
    """
    Generate a list of date periods for a given scheduler ID.

    Args:
        scheduler_id (str): The ID of the scheduler.

    Returns:
        list: A list of date periods in the format "start_date=<date>&end_date=<date>".
    """
    date_now = datetime.date.today()
    date_periods = []
    if scheduler_id == "2h":
        # daily run takes 5 days
        days = 5
    if scheduler_id == "7d":
        # weekly run takes 14 days
        days = 14
    if scheduler_id == "1m":
        # monthly run takes 30 days
        days = 30
    for i in range(days):
        start_date = date_now - datetime.timedelta(days=i)
        end_date = date_now - datetime.timedelta(days=i)
        date_period = f"start_date={start_date}&end_date={end_date}"
        date_periods.append(date_period)
    return date_periods


def build_urls(scheduler_id):
    """
    Builds a list of URLs for the FASS API based on the provided scheduler ID.

    Args:
        scheduler_id (str): The ID of the scheduler. Valid values are "2h", "7d", and "1m".

    Returns:
        list: A list of URLs for the FASS API.

    Notes:
        - The function retrieves the app token from Google Cloud Secret Manager.
        - The function constructs the base URL based on the configuration.
        - The function determines the date periods based on the scheduler ID.
        - The function appends the date periods to the base URL to form the final URLs.
        - The function raises a RuntimeError if an error occurs.
    """
    urls = []
    base_url = f"{config['base_url']}?"
    try:
        if scheduler_id not in ["2h", "7d", "1m"]:
            e = write_log("Scheduler ID not valid", None, severity="ERROR")

        date_periods = _get_date_periods(scheduler_id)
        for date_period in date_periods:
            urls.append((base_url + date_period).strip())
    except:
        raise RuntimeError()
    return urls


def run_execution(executor_url, urls, datetime_now, scheduler_id):
    """
    Runs the execution of the FASS API for the given list of URLs.

    This function takes the list of URLs and runs them in parallel by sending
    an asynchronous POST request to the Executor Cloud Function. The Executor
    Cloud Function will then call the FASS API and write the data to either
    GCS (for 7d and 1m schedulers) or BigQuery (for 2h scheduler).

    The function also sets the destination and batch_load flags depending on
    the scheduler ID and the position of the URL in the list.

    Args:
        executor_url (str): The URL of the Executor Cloud Function.
        urls (list): The list of URLs to run.
        datetime_now (str): The current datetime in ISO format.
        scheduler_id (str): The ID of the scheduler.

    Returns:
        None
    """
    last_url = urls[-1]
    # Always False beside for last URL in 1m and 7d schedulers
    batch_load = False
    print(write_log("Sending async POST requests"))
    for url in urls:
        if url == last_url:
            # At the last processed URL, load temp CSV from GCS to BigQuery
            batch_load = True
        start_date = url.split("start_date=")[1].split("&")[0]
        data = {
            "url": url,
            "datetime_now": datetime_now,
            "start_date": start_date,
            "batch_load": batch_load,
            "scheduler_id": scheduler_id,
        }
        _post_with_url(executor_url, data)
        time.sleep(15)
    return

def check_running_routines(bucket_name, folder_name):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=folder_name)
    return any(blob.name != folder_name for blob in blobs)

def check_files_count(bucket_name, scheduler_id):
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
    

    all_files = [
            f"{bucket_name}/{blob.name}"
            for blob in client.list_blobs(bucket_name, prefix="temp_data")
        ]
    print(
        write_log(
            f"Expected {expected_num_files} files, found {len(all_files)} files in GCS bucket"
            )
        )
    return len(all_files) == expected_num_files
        
    