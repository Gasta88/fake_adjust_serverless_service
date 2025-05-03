import unittest
import json


class CheckTerraformPlan(unittest.TestCase):
    """Test suite to check the layout of the Terraform deployment from the JSON plan."""

    maxDiff = None

    def setUp(self):
        with open("../../deploy/plan.json") as f:
            self.plan = json.load(f)

    def test_landing_bucket(self):
        """Test configuration of GCS landing bucket."""
        buckets = {
            resource["address"]: resource
            for resource in self.plan["planned_values"]["root_module"]["resources"]
            if resource["type"] == "google_storage_bucket"
        }
        landing_bucket = buckets.get("google_storage_bucket.gcf_storage", None)
        self.assertIsNotNone(landing_bucket)
        # add more tests if more buckets are created

    def test_schedulers(self):
        """Test configuration of Cloud Schedulers."""
        schedulers = {
            resource["address"]: resource
            for resource in self.plan["planned_values"]["root_module"]["resources"]
            if resource["type"] == "google_cloud_scheduler_job"
        }
        scheduler_2h = schedulers.get("google_cloud_scheduler_job.every_2_hours", None)
        self.assertIsNotNone(scheduler_2h)
        scheduler_7d = schedulers.get("google_cloud_scheduler_job.every_7_days", None)
        self.assertIsNotNone(scheduler_7d)
        scheduler_1m = schedulers.get("google_cloud_scheduler_job.every_1_month", None)
        self.assertIsNotNone(scheduler_1m)

    def test_functions(self):
        """Test configuration of Cloud Functions."""
        schedulers = {
            resource["address"]: resource
            for resource in self.plan["planned_values"]["root_module"]["resources"]
            if resource["type"] == "google_cloudfunctions2_function"
        }
        orchestrator = schedulers.get(
            "google_cloudfunctions2_function.orchestrator_function", None
        )
        self.assertIsNotNone(orchestrator)
        executor = schedulers.get(
            "google_cloudfunctions2_function.executor_function", None
        )
        self.assertIsNotNone(executor)


if __name__ == "__main__":
    runner = unittest.TextTestRunner(verbosity=3)
    unittest.main(testRunner=runner)
