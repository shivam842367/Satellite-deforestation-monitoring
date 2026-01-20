import ee
import json
import os

def init_ee():
    key_json = os.environ["EE_SERVICE_KEY"]   # STRING
    key = json.loads(key_json)

    credentials = ee.ServiceAccountCredentials(
        key["client_email"],
        key_data=key_json
    )

    ee.Initialize(credentials)
