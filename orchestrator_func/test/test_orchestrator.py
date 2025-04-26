import unittest
from orchestrator_func.utils.read import (
    build_urls,
    run_execution,
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
        scheduler_id = "2h"
        first_start_date = (
            datetime.datetime.now() - datetime.timedelta(days=4)
        ).strftime("%Y-%m-%d")
        res = build_urls(scheduler_id)
        self.assertTrue(len(res) == 5)
        self.assertEqual(
            res[-1],
            f"https://fass-api-874544665874.us-central1.run.app/reporting?start_date={first_start_date}&end_date={first_start_date}",
        )
        scheduler_id = "7d"
        first_start_date = (
            datetime.datetime.now() - datetime.timedelta(days=13)
        ).strftime("%Y-%m-%d")
        res = build_urls(scheduler_id)
        self.assertTrue(len(res) == 14)
        scheduler_id = "1m"
        res = build_urls(scheduler_id)
        self.assertTrue(len(res) == 30)


    @patch("google.auth.transport.requests.Request")
    @patch("google.oauth2.id_token.fetch_id_token")
    def test_run_execution(self, mock_req, mock_fit):
        executor_url = "https://example-project.cloudfunctions.net/my-function"
        token = "my_awesome_token"
        mock_fit.return_value = token
        urls = [f"my/first/awesome/url&start_date={self.today_date}&end_date={self.today_date}"]
        scheduler_id = "2h"
        run_execution(executor_url, urls, self.today_datetime, scheduler_id)
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
