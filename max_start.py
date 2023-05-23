import boto3
import dataset
import requests
import json 

rds = boto3.client('rds')
db_rds = rds.describe_db_instances()['DBInstances'][0]
ENDPOINT = db_rds['Endpoint']['Address']
PORT = db_rds['Endpoint']['Port']
db_url = 'mysql+mysqlconnector://{}:{}@{}:{}/books'.format('username',
                                                           'password',
                                                           ENDPOINT,
                                                           PORT)
db = dataset.connect(db_url)
api_key = "AIzaSyDg2HWJtiz4KVc0zHvY50a-rsoUDUm0Sbw"
url = "https://www.googleapis.com/books/v1/volumes"


def lambda_handler_index(event, context):
    category = event['category']
    max_start_index = 0

    while True:
        parameters = {
            "q": category,
            "key": api_key,
            "printType": "books",
            "maxResults": 40,
            "startIndex": max_start_index
        }
        response = requests.get(url, params=parameters)

        # 2 possible useless requests: status_code=400 or total item=0
        if response.status_code == 200:
            response_content = response.json()
            total_items = response_content.get('totalItems', 0)

            if total_items == 0:
                break
            max_start_index += 20

        elif response.status_code == 400:
            print(response)
            break

    db['category_info'].upsert({'category': category, 'max_index': max_start_index}, ['category'])

    return {
        "statusCode": 200
    }
