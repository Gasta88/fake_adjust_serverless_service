import unittest
import datetime
from unittest.mock import patch, Mock, MagicMock
import pandas as pd
from executor_func.utils.read import (
    get_with_url,
    clean_raw_data,
    get_bq_dataset,
    get_bq_tables,
    get_temp_prefix,
    get_all_temp_files,
)
from executor_func.utils.write import (
    write_raw_to_bq,
    update_day_table,
)


class ExecutorTestCase(unittest.TestCase):
    """Test suite for executor function"""

    maxDiff = None

    def setUp(self):
        self.today_date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.today_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def tearDown(self):
        pass

    def _mock_response(
        self, status=200, content="CONTENT", json_data=None, raise_for_status=None
    ):
        """
        since we typically test a bunch of different
        requests calls for a service, we are going to do
        a lot of mock responses, so its usually a good idea
        to have a helper function that builds these things
        """
        mock_resp = Mock()
        # mock raise_for_status call w/optional error
        mock_resp.raise_for_status = Mock()
        if raise_for_status:
            mock_resp.raise_for_status.side_effect = raise_for_status
        # set status code and content
        mock_resp.status_code = status
        mock_resp.content = content
        # add json data if provided
        if json_data:
            mock_resp.json = Mock(return_value=json_data)
        return mock_resp

    @patch("requests.get")
    def test_get_with_url(self, mock_get):
        """Test get_with_url function"""
        url = "https://example.com/api/data"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"key": "value"}]
        mock_get.return_value = mock_response

        # Test the function
        result = get_with_url(url)

        # Assert the result
        self.assertEqual(result, [{"key": "value"}])
        mock_get.assert_called_once_with(url, timeout=900) 

    def test_clean_raw_data(self):
        "Test clean_raw_data function"
        data = [
            {
                "installs": 1,
                "limit_ad_tracking_installs": 1,
                "clicks": 1,
                "impressions": 1,
                "ad_spend": 0.1,
                "ad_network_name": "facebook",
                "campaign_name": "campaign1",
                "country_code": "it",
                "platform": "android",
                "creative_name": "creative1",
                "uninstalls": 1,
                "click_convertion_rate": 1.0,
                "click_through_rate": 1.0,
                "impressions_convertion_rate": 1.0,
                "start_date": self.today_date,
                "end_date": self.today_date,
            },
            {
                "installs": 2,
                "limit_ad_tracking_installs": 2,
                "clicks": 2,
                "impressions": 2,
                "ad_spend": 0.2,
                "ad_network_name": "facebook",
                "campaign_name": "campaign2",
                "country_code": "it",
                "platform": "android",
                "creative_name": "creative2",
                "uninstalls": 2,
                "click_convertion_rate": 0.5,
                "click_through_rate": 0.5,
                "impressions_convertion_rate": 0.5,
                "start_date": self.today_date,
                "end_date": self.today_date,
            },
        ]

        # Expected result
        expected_result = pd.DataFrame(
            [
                {
                    "adNetworkName": "facebook",
                    "campaignName": "campaign1",
                    "creativeName": "creative1",
                    "startDate": self.today_date,
                    "endDate": self.today_date,
                    "platform": "android",
                    "installs": 1,
                    "adSpend": 0.1,
                    "clicks": 1,
                    "impressions": 1,
                    "clickConvertionRate": 1.0,
                    "clickThroughRate": 1.0,
                    "impressionsConvertionRate": 1.0,
                    "limitAdTrackingInstalls": 1,
                    "uninstalls": 1,
                    "createdAt": pd.to_datetime(self.today_datetime),
                },
                {
                    "adNetworkName": "facebook",
                    "campaignName": "campaign2",
                    "creativeName": "creative2",
                    "startDate": self.today_date,
                    "endDate": self.today_date,
                    "platform": "android",
                    "installs": 2,
                    "adSpend": 0.2,
                    "clicks": 2,
                    "impressions": 2,
                    "clickConvertionRate": 0.5,
                    "clickThroughRate": 0.5,
                    "impressionsConvertionRate": 0.5,
                    "limitAdTrackingInstalls": 2,
                    "uninstalls": 2,
                    "createdAt": pd.to_datetime(self.today_datetime),
                },
            ]
        )
        # Test the function
        result = clean_raw_data(data, self.today_datetime)
        # Assert the result
        pd.testing.assert_frame_equal(result, expected_result)


    def test_get_bq_dataset(self):
        """Test get_bq_dataset function"""
        function_name = "my-cloud-function-dev"
        expected = "analytics_test"
        res = get_bq_dataset(function_name)
        self.assertEqual(res, expected)

        function_name = "my-cloud-function-prod"
        expected = "analytics"
        res = get_bq_dataset(function_name)
        self.assertEqual(res, expected)

        self.assertRaises(ValueError, get_bq_dataset, "not_my_cloud_function")

    def test_get_bq_tables(self):
        """Test get_bq_tables function"""
        project_id = "eighth-duality-457819-r4"
        dataset_name = "analytics_test"
        expected_raw_id = (
            f"{project_id}.{dataset_name}.fass_raw"
        )
        expected_day_id = (
            f"{project_id}.{dataset_name}.fass_day"
        )
        res_raw, res_day = get_bq_tables(dataset_name)
        self.assertEqual(res_raw, expected_raw_id)
        self.assertEqual(res_day, expected_day_id)

    def test_get_temp_prefix(self):
        """Test get_temp_prefix function"""
        bucket_name = "eighth-duality-457819-r4"
        start_date = "2024-01-01"
        platform = "android"
        expected = "eighth-duality-457819-r4/temp_data/android/fass_data_2024_01_01.csv"
        res = get_temp_prefix(bucket_name, start_date, platform)
        self.assertEqual(res, expected)

    @patch("google.cloud.storage.Client")
    def test_get_all_temp_files(self, mock_obj):
        """Test get_all_temp_files function"""

        def _create_mock_blob(prefix_name):
            """Helper function to create a mock blob"""
            mock_blob = Mock()
            mock_blob.name = prefix_name
            return mock_blob

        mock_gcs = mock_obj.return_value
        bucket_name = "eighth-duality-457819-r4"
        scheduler_id = "7d"
        expected = [
            "eighth-duality-457819-r4/temp_data/android/fass_data_2024_01_01.csv",
            "eighth-duality-457819-r4/temp_data/android/fass_data_2024_01_02.csv",
            "eighth-duality-457819-r4/temp_data/android/fass_data_2024_01_03.csv",
            "eighth-duality-457819-r4/temp_data/android/fass_data_2024_01_04.csv",
            "eighth-duality-457819-r4/temp_data/android/fass_data_2024_01_05.csv",
            "eighth-duality-457819-r4/temp_data/android/fass_data_2024_01_06.csv",
            "eighth-duality-457819-r4/temp_data/android/fass_data_2024_01_07.csv",
            "eighth-duality-457819-r4/temp_data/android/fass_data_2024_01_08.csv",
            "eighth-duality-457819-r4/temp_data/android/fass_data_2024_01_09.csv",
            "eighth-duality-457819-r4/temp_data/android/fass_data_2024_01_10.csv",
            "eighth-duality-457819-r4/temp_data/android/fass_data_2024_01_11.csv",
            "eighth-duality-457819-r4/temp_data/android/fass_data_2024_01_12.csv",
            "eighth-duality-457819-r4/temp_data/android/fass_data_2024_01_13.csv",
            "eighth-duality-457819-r4/temp_data/android/fass_data_2024_01_14.csv",
            "eighth-duality-457819-r4/temp_data/ios/fass_data_2024_01_01.csv",
            "eighth-duality-457819-r4/temp_data/ios/fass_data_2024_01_02.csv",
            "eighth-duality-457819-r4/temp_data/ios/fass_data_2024_01_03.csv",
            "eighth-duality-457819-r4/temp_data/ios/fass_data_2024_01_04.csv",
            "eighth-duality-457819-r4/temp_data/ios/fass_data_2024_01_05.csv",
            "eighth-duality-457819-r4/temp_data/ios/fass_data_2024_01_06.csv",
            "eighth-duality-457819-r4/temp_data/ios/fass_data_2024_01_07.csv",
            "eighth-duality-457819-r4/temp_data/ios/fass_data_2024_01_08.csv",
            "eighth-duality-457819-r4/temp_data/ios/fass_data_2024_01_09.csv",
            "eighth-duality-457819-r4/temp_data/ios/fass_data_2024_01_10.csv",
            "eighth-duality-457819-r4/temp_data/ios/fass_data_2024_01_11.csv",
            "eighth-duality-457819-r4/temp_data/ios/fass_data_2024_01_12.csv",
            "eighth-duality-457819-r4/temp_data/ios/fass_data_2024_01_13.csv",
            "eighth-duality-457819-r4/temp_data/ios/fass_data_2024_01_14.csv",
        ]

        mock_gcs.list_blobs.return_value = [
            _create_mock_blob("temp_data/android/fass_data_2024_01_01.csv"),
            _create_mock_blob("temp_data/android/fass_data_2024_01_02.csv"),
            _create_mock_blob("temp_data/android/fass_data_2024_01_03.csv"),
            _create_mock_blob("temp_data/android/fass_data_2024_01_04.csv"),
            _create_mock_blob("temp_data/android/fass_data_2024_01_05.csv"),
            _create_mock_blob("temp_data/android/fass_data_2024_01_06.csv"),
            _create_mock_blob("temp_data/android/fass_data_2024_01_07.csv"),
            _create_mock_blob("temp_data/android/fass_data_2024_01_08.csv"),
            _create_mock_blob("temp_data/android/fass_data_2024_01_09.csv"),
            _create_mock_blob("temp_data/android/fass_data_2024_01_10.csv"),
            _create_mock_blob("temp_data/android/fass_data_2024_01_11.csv"),
            _create_mock_blob("temp_data/android/fass_data_2024_01_12.csv"),
            _create_mock_blob("temp_data/android/fass_data_2024_01_13.csv"),
            _create_mock_blob("temp_data/android/fass_data_2024_01_14.csv"),
            _create_mock_blob("temp_data/ios/fass_data_2024_01_01.csv"),
            _create_mock_blob("temp_data/ios/fass_data_2024_01_02.csv"),
            _create_mock_blob("temp_data/ios/fass_data_2024_01_03.csv"),
            _create_mock_blob("temp_data/ios/fass_data_2024_01_04.csv"),
            _create_mock_blob("temp_data/ios/fass_data_2024_01_05.csv"),
            _create_mock_blob("temp_data/ios/fass_data_2024_01_06.csv"),
            _create_mock_blob("temp_data/ios/fass_data_2024_01_07.csv"),
            _create_mock_blob("temp_data/ios/fass_data_2024_01_08.csv"),
            _create_mock_blob("temp_data/ios/fass_data_2024_01_09.csv"),
            _create_mock_blob("temp_data/ios/fass_data_2024_01_10.csv"),
            _create_mock_blob("temp_data/ios/fass_data_2024_01_11.csv"),
            _create_mock_blob("temp_data/ios/fass_data_2024_01_12.csv"),
            _create_mock_blob("temp_data/ios/fass_data_2024_01_13.csv"),
            _create_mock_blob("temp_data/ios/fass_data_2024_01_14.csv"),
        ]
        res = get_all_temp_files(bucket_name, scheduler_id)
        self.assertEqual(res, expected)

    @unittest.skip
    def test_get_temp_df(self):
        """Test get_temp_df function"""

    @patch("pandas_gbq.to_gbq")
    def test_write_raw_to_bq(self, mock_to_gbq):
        """Test write_raw_to_bq function"""
        df = pd.DataFrame(
            [
                {
                    "installs": 1,
                    "limitAdTrackingInstalls": 1,
                    "clicks": 1,
                    "impressions": 1,
                    "ad_spend": 0.1,
                    "startDate": "2024-01-01",
                    "createdAt": pd.to_datetime(self.today_datetime),
                }
            ]
        )
        table_id = "analytics_test.fass_raw"
        mock_to_gbq.return_value = None
        write_raw_to_bq(df, table_id)
        mock_to_gbq.assert_called_with(
            df, table_id, project_id="eighth-duality-457819-r4", if_exists="append"
        )

    @patch("google.cloud.bigquery.Client")
    def test_update_day_table(self, mock_obj):
        """Test update_day_table function"""
        mock_bq = mock_obj.return_value
        all_files = [
            "eighth-duality-457819-r4/temp_data/android/fass_data_2024_01_01.csv",
            "eighth-duality-457819-r4/temp_data/ios/fass_data_2024_01_01.csv",
        ]
        table_id = "analytics_test.fass_day"
        update_day_table(all_files, self.today_datetime, table_id)
        mock_bq.query.assert_called_with(
            f"""INSERT INTO {table_id}
                                (reportDay, updatedAt)  
                                VALUES ('2024-01-01', '{self.today_datetime}')
            """
        )


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=3)
    unittest.main(testRunner=runner)
