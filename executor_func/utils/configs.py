# Main configuration for the Python script and Adjust Report API interaction

config = {
    "project_id": "justplay-data",
    "table_raw_name": "adjust_spend_report_by_channel_raw",
    "table_day_name": "adjust_spend_report_by_channel_day",
    "integer_cols": ["installs", "limit_ad_tracking_installs", "clicks", "impressions"],
    "ordered_columns": [
        "channel",
        "campaign",
        "countryCode",
        "reportDay",
        "osName",
        "creative",
        "installs",
        "cost",
        "clicks",
        "impressions",
        "limitAdTrackingInstalls",
        "createdAt",
    ],
    "float_cols": ["cost"],
    "timeout_limit_seconds": 900,
}
