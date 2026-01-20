import ee
import json

with open("ee-key.json", "r") as f:
    key_json = f.read()              # STRING
    key = json.loads(key_json)       # dict (for email only)

credentials = ee.ServiceAccountCredentials(
    key["client_email"],
    key_data=key_json                # STRING, not dict
)

ee.Initialize(credentials)

print("Earth Engine initialized successfully!")
print(
    ee.ImageCollection("COPERNICUS/S2_SR")
      .first()
      .bandNames()
      .getInfo()
)
