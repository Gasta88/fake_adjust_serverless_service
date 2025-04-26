# Main configuration for the Python script and Adjust Report API interaction

config = {
    "project_id": "eighth-duality-457819-r4",
    "table_raw_name": "adjust_spend_report_by_channel_raw",
    "table_day_name": "adjust_spend_report_by_channel_day",
    "integer_cols": ["installs", "limit_ad_tracking_installs", "clicks", "impressions", "uninstalls"],
    "ordered_columns": [
        "ad_network_name",
        "campaign_name",
        "creative_name",
        "start_date",
        "end_date",
        "platform",
        "installs",
        "ad_spend",
        "clicks",
        "impressions",
        "click_convertion_rate",
        "click_through_rate",
        "impressions_convertion_rate",
        "limit_ad_tracking_installs",
        "uninstalls",
    ],
    "float_cols": ["ad_spend", "click_convertion_rate","click_through_rate","impressions_convertion_rate"],
    "timeout_limit_seconds": 900,
}
