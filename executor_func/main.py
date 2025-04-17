import functions_framework
from utils.write import (
    write_log,
    write_raw_to_bq,
    update_day_table,
)
import os
import pandas as pd
from utils.read import (
    get_with_url,
    clean_raw_data,
    get_bq_dataset,
    get_bq_tables,
    get_temp_prefix,
    get_all_temp_files,
    get_temp_df,
)

GCS_BUCKET = os.environ.get("GCS_BUCKET", "GCS_BUCKET not set")


# Register an HTTP function with the Functions Framework
@functions_framework.http
def call_adjust_api(request):
    args = request.get_json(silent=True)
    print(write_log(f"Start function on {args['start_date']}", f"Args: {args}"))
    if args:
        function_name = os.environ.get("K_SERVICE", "")
        dataset_name = get_bq_dataset(function_name)
        table_raw_id, table_day_id = get_bq_tables(dataset_name)
        for platform in ["ios", "android"]:
            final_url = f"{args['url']}&os_name__in={platform}"
            print(
                write_log(
                    f"Fetching data for {platform} on {args['start_date']}",
                    f"url: {final_url}",
                )
            )
            results = get_with_url(final_url, args["adjust_api_key"])
            if len(results) == 0:
                print(
                    write_log(
                        "No data found",
                        f"{args['start_date']} on {platform}",
                        severity="WARNING",
                    )
                )
                # If a data file is missing, place a dummy one in GCS as warning
                df_empty = pd.DataFrame([{"id": "empty"}])
                empty_prefix = f"gs://{GCS_BUCKET}/temp_data/{args['start_date']}/{platform}/NO_DATA.csv"
                df_empty.to_csv(empty_prefix, index=False)
                continue
            df_raw = clean_raw_data(results, args["datetime_now"])
            print(write_log("Retrieved and cleaned data", f"DF shape: {df_raw.shape}"))
            print(write_log("Writing data to GCS"))
            temp_prefix = get_temp_prefix(GCS_BUCKET, args["start_date"], platform)
            print(write_log(f"Writing {temp_prefix}"))
            df_raw.to_csv(f"gs://{temp_prefix}", index=False)
        if args["batch_load"]:
            print(write_log("Batch load GCS data to BigQuery"))
            all_files = get_all_temp_files(GCS_BUCKET, args["scheduler_id"])
            if len(all_files) == 0:
                print(write_log("No data found in temp folder", "", severity="WARNING"))
                raise Exception("No data found in temp folder")
            # Sometimes Adjust fails and we get no data files. Stop processing if this happens
            empty_files = [f for f in all_files if "NO_DATA" in f]
            if len(empty_files) > 0:
                print(
                    write_log(
                        "Missing file from Adjust. Clean temp data from GCS",
                        "/n".join(empty_files),
                        severity="WARNING",
                    )
                )
                
                print(write_log(f"End function on {args['start_date']}"))
                return "Done"
            temp_raw_df = get_temp_df(all_files)
            write_raw_to_bq(temp_raw_df, table_raw_id)
            print(write_log("Update day table on BigQuery"))
            update_day_table(all_files, args["datetime_now"], table_day_id)
            
    else:
        print(write_log("No args found", f"Args: {args}", severity="ERROR"))
    print(write_log(f"End function on {args['start_date']}"))
    return "Done"
