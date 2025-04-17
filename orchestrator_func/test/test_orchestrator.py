import unittest
from orchestrator_func.utils.read import (
    build_urls,
    run_execution,
    get_gcp_secret_value,
    check_running_routines
)
import datetime
from unittest.mock import patch,MagicMock


class OrcheatratorTestCase(unittest.TestCase):
    """Test suite for orchestrator function"""

    maxDiff = None

    def setUp(self):
        self.today_date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.today_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def tearDown(self):
        pass

    def test_build_urls(self):
        """Test build_urls function"""
        app_token = "super_secret_token"
        scheduler_id = "2h"
        first_start_date = (
            datetime.datetime.now() - datetime.timedelta(days=4)
        ).strftime("%Y-%m-%d")
        res = build_urls(scheduler_id, app_token)
        self.assertTrue(len(res) == 5)
        self.assertEqual(
            res[-1],
            f"https://dash.adjust.com/control-center/reports-service/report?app_token=super_secret_token&ad_spend_mode=mixed&attribution_type=all&dimensions=channel,campaign,creative,country_code,os_name,day&metrics=installs,cost,clicks,impressions,limit_ad_tracking_installs&date_period={first_start_date}:{first_start_date}",
        )
        scheduler_id = "7d"
        first_start_date = (
            datetime.datetime.now() - datetime.timedelta(days=13)
        ).strftime("%Y-%m-%d")
        res = build_urls(scheduler_id, app_token)
        self.assertTrue(len(res) == 14)
        self.assertEqual(
            res[-1],
            f"https://dash.adjust.com/control-center/reports-service/report?app_token=super_secret_token&ad_spend_mode=mixed&attribution_type=all&dimensions=channel,campaign,creative,country_code,os_name,day&metrics=installs,cost,clicks,impressions,limit_ad_tracking_installs&date_period={first_start_date}:{first_start_date}",
        )
        scheduler_id = "1m"
        res = build_urls(scheduler_id, app_token)
        self.assertTrue(len(res) == 30)

    @patch("orchestrator_func.utils.read.secretmanager.SecretManagerServiceClient")
    def test_get_gcp_secret_value(self, mock_smc):
        """Test get_gcp_secret_value function"""
        mock_smc.return_value.access_secret_version.return_value.payload.data = (
            b"super_secret_token"
        )
        res = get_gcp_secret_value("adjust_app_token")
        self.assertEqual(res, "super_secret_token")

    @patch("google.auth.transport.requests.Request")
    @patch("google.oauth2.id_token.fetch_id_token")
    def test_run_execution(self, mock_req, mock_fit):
        executor_url = "https://example-project.cloudfunctions.net/my-function"
        token = "my_awesome_token"
        mock_fit.return_value = token
        api_key = "my_awesome_api_key"
        urls = [f"my/first/awesome/url&date_period={self.today_date}:{self.today_date}"]
        scheduler_id = "2h"
        run_execution(api_key, executor_url, urls, self.today_datetime, scheduler_id)
        mock_req.assert_called_once_with(
            token,
            executor_url,
        )
    
    @patch("orchestrator_func.utils.read.storage.Client")
    def test_check_running_routines_files_present(self, mock_storage_client):
        """Test check_running_routines when files are present"""
        mock_bucket = MagicMock()
        mock_blob1 = MagicMock()
        mock_blob2 = MagicMock()

        mock_blob1.name = "temp_data/adjust_android_file1.csv"
        mock_blob2.name = "temp_data/adjust_ios_file1.csv"

        mock_bucket.list_blobs.return_value = [mock_blob1, mock_blob2]
        mock_storage_client.return_value.get_bucket.return_value = mock_bucket

        result = check_running_routines("test-bucket", "temp_data/")
        self.assertTrue(result)

    @patch("orchestrator_func.utils.read.storage.Client")
    def test_check_running_routines_no_files(self, mock_storage_client):
        """Test check_running_routines when no files are present"""
        mock_bucket = MagicMock()
        mock_bucket.list_blobs.return_value = []  
        mock_storage_client.return_value.get_bucket.return_value = mock_bucket

        result = check_running_routines("test-bucket", "temp_data/")
        self.assertFalse(result)

    @patch("orchestrator_func.utils.read.storage.Client")
    def test_check_running_routines_only_folder_present(self, mock_storage_client):
        """Test check_running_routines when only the folder exists"""
        mock_bucket = MagicMock()
        mock_blob = MagicMock()

        mock_blob.name = "temp_data/"  
        mock_bucket.list_blobs.return_value = [mock_blob]
        mock_storage_client.return_value.get_bucket.return_value = mock_bucket

        result = check_running_routines("test-bucket", "temp_data/")
        self.assertFalse(result)



if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=3)
    unittest.main(testRunner=runner)
