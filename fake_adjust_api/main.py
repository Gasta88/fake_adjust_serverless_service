from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List
import uvicorn
import random
import faker

app = FastAPI()
fake = faker.Faker()
AD_NETWORKS = [
    "Google AdMob",
    "Facebook Audience Network",
    "Unity Ads",
    "InMobi",
    "AppLovin",
    "AdColony",
    "Vungle",
    "IronSource",
    "Chartboost",
    "Tapjoy",
    "AdMob Mediation",
    "AdThrive",
    "Fyber",
    "Mintegral",
    "AdTiming",
    "StartApp",
    "AdDuplex",
    "Liftoff",
    "Smaato",
    "AdYouLike"
]


class ReportingResponse(BaseModel):
    installs: int
    ad_spend: float
    clicks: int
    impressions: int
    click_convertion_rate: float
    click_through_rate: float
    impressions_convertion_rate: float
    limit_ad_tracking_installs: int
    uninstalls: int
    campaign_name: str
    creative_name: str
    ad_network_name: str
    start_date: str
    end_date: str
    platform: str

@app.get("/reporting", response_model=List[ReportingResponse])
def get_reporting(
    start_date: str = Query(..., example="2025-05-01"),
    end_date: str = Query(..., example="2025-05-01"),
    platform: str = Query(..., example="ios", regex="^(ios|android)$")
):
    data = []
    for _ in range(random.randint(1, 10)):
    # Generate fake data based on the query parameters
        installs = random.randint(1000, 10000)
        ad_spend = random.uniform(0.01, 1000.00)
        clicks = random.randint(100, 1000)
        impressions = random.randint(100, 1000)
        limit_ad_tracking_installs = random.randint(10, 100)
        uninstalls = random.randint(1000, 10000)
        campaign_name = fake.bs()
        creative_name = fake.catch_phrase()
        ad_network_name = random.choice(AD_NETWORKS)
        start_date = start_date
        end_date = end_date

        data.append(
            ReportingResponse(
                installs=installs,
                ad_spend=ad_spend,
                clicks=clicks,
                impressions=impressions,
                click_convertion_rate=(installs / clicks) * 100 if clicks > 0 else 0,
                click_through_rate=(clicks / impressions) * 100 if impressions > 0 else 0,
                impressions_convertion_rate=(installs / impressions) * 100 if impressions > 0 else 0,
                limit_ad_tracking_installs=limit_ad_tracking_installs,
                uninstalls=uninstalls,
                campaign_name=campaign_name,
                creative_name=creative_name,
                ad_network_name=ad_network_name,
                start_date=start_date,
                end_date=end_date,
                platform=platform
            )
        )
    return data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)