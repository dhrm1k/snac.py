import os
import requests
from dotenv import load_dotenv

load_dotenv()

SNAC_HOST = os.getenv("SNAC_HOST")
API_TOKEN = os.getenv("API_TOKEN")


# More about getting the api token here https://comam.es/snac-doc/snac.1.html#Implementing_post_bots
# Connect to this URL: https://$SNAC_HOST/oauth/x-snac-get-token

def post_status(content):
    url = f"{SNAC_HOST}/api/v1/statuses"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    data = {"status": content}

    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200 or response.status_code == 201:
        print("Post successful!")
    else:
        print(f"Error: {response.status_code}, {response.text}")


post_status("Hello from snac.py!")
