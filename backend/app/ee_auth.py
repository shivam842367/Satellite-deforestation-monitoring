import ee
import json
import os

def init_ee():
    try:
        key_json = os.getenv("EE_SERVICE_ACCOUNT_KEY")

        if key_json:
            key_dict = json.loads(key_json)
            credentials = ee.ServiceAccountCredentials(
                key_dict["client_email"],
                key_data=key_json
            )
            ee.Initialize(credentials)
        else:
            ee.Initialize()
    except Exception as e:
        raise RuntimeError(
            "Earth Engine not initialized. "
            "Run: earthengine authenticate && earthengine set_project <PROJECT_ID>"
        ) from e
