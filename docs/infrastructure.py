from diagrams import Cluster, Diagram
from diagrams.gcp.devtools import Scheduler
from diagrams.gcp.compute import GCF
from diagrams.gcp.analytics import BigQuery
from diagrams.custom import Custom

# graph_attr = {"bgcolor": "aliceblue"}

with Diagram("FakeAdjust Serverless Service", show=False):

    orchestrator = GCF("Orchestrator")

    cc_adjust = Custom("Fake Adjust REST API", "./adjust_icon.png")

    bq = BigQuery("Analytics dataset")

    with Cluster("Schedulers Pool"):
        scheduler_2h = Scheduler("Every 2h")
        scheduler_7d = Scheduler("Every 7d")
        scheduler_1m = Scheduler("Every 1m")

    with Cluster("Functions Pool"):
        executor_1 = GCF("Executor_1")
        executor_n = GCF("Executor_n")

    scheduler_7d >> orchestrator >> executor_1 >> cc_adjust >> executor_n >> bq
