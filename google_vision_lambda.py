"""
Author: Ryan Liang
This is the lambda function that will be used to call the Google Vision API.
This function will be triggered by the S3 bucket when a new json of image is uploaded,
and the output will be stored in another S3 bucket.
The image parquets was preprocessed into format of {label: label, image_url: image_url}
from the original parquet.
"""

import os
import json
import requests
from google.cloud import vision

API_KEY = 'AIzaSyCTtwcZvAV4y-gE3I6gaz61h1ziLhDxQu8'
client = vision.ImageAnnotatorClient(client_options={"api_key": API_KEY})

def lambda_handler(event, context):
    image_label = str(event['label'])
    image_url = str(event['image_url'])
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            byte_image = response.content
            image = vision.Image(content=byte_image)
            response = client.label_detection(image=image, max_results=50)
    except Exception as e:
        print(e)


