import functions_framework
from utils.write import write_log
from utils.read import build_urls, run_execution,check_running_routines
import os
import datetime
import time

from utils.read import (
    check_files_count
)
from utils.write import (
    clean_all_temp_files
)


EXECUTOR_URL = os.environ.get("EXECUTOR_URL", "EXECUTOR_URL not set")
DATETIME_NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
GCS_BUCKET = os.environ.get("GCS_BUCKET", "GCS_BUCKET not set")


# Register an HTTP function with the Functions Framework
@functions_framework.http
def handle_api_calls(request):
    args = request.get_json(silent=True)
    print(write_log("Start function", f"Args: {args}"))
    
    if check_running_routines(GCS_BUCKET, "temp_data"):
        print(write_log("Currently lock is acquired by another job. Skipping current execution"))
        print(write_log("End function"))
        return "Done"


    if args:
        print(write_log(f'Build urls for schedule {args["scheduler_id"]}'))
        urls = build_urls(args["scheduler_id"])
        print(write_log("Generated urls", f"Urls: {urls}"))
        run_execution(EXECUTOR_URL, urls, DATETIME_NOW, args["scheduler_id"])
        
        count = 0
        cleaned = False

        while count < 60:
            
            if check_files_count(GCS_BUCKET, args["scheduler_id"]):
                time.sleep(120)
                clean_all_temp_files(GCS_BUCKET)
                print(write_log("Clean temp data from GCS"))
                cleaned = True
                break
            
            time.sleep(30)
            count += 1

        if not cleaned:
            clean_all_temp_files(GCS_BUCKET)
            print(write_log("Clean temp data from GCS"))
    else:
        print(write_log("No args found", f"Args: {args}", severity="ERROR"))
    print(write_log("End function"))
    return "Done"
