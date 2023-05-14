import boto3
import dataset
import json
import requests

api_key = 'AIzaSyBgPYASTWnKJfz_eNzjuywNHMUt6cZV2xY'
rds = boto3.client('rds')
db_rds = rds.describe_db_instances()['DBInstances'][0] 
ENDPOINT = db_rds['Endpoint']['Address']
PORT = db_rds['Endpoint']['Port']
db_url = 'mysql+mysqlconnector://{}:{}@{}:{}/books'.format(
    'username',
    'password',
    ENDPOINT,
    PORT)
db = dataset.connect(db_url)


def search_books(start_year, end_year):
    ''' 
    Scrape all books published in a given period of time
    '''

    url = "https://www.googleapis.com/books/v1/volumes"
    parameters = {
        "q": "",
        "key": api_key,
        "printType": "books",
        "startIndex": 0
    }
    books = []

    for year in range(start_year, end_year+1):
        parameters["q"] = f"pubdate:{year}"
        response = requests.get(url, params=parameters)
        if response.status_code == 200:
            results = json.loads(response.content)
            books.extend(results["items"])
        else:
            print(f"Failed to fetch results for year {year}.")
    return books


def store_books_in_db(books):
    ''' 
    Helper function to store all scraped books into db
    '''

    table = db['book_info']

    for book in books:
        book_info = {
            'book_id': book['id'],
            'title': book['volumeInfo']['title'] if 'title' in book['volumeInfo'] else None,
            'subtitle': book['volumeInfo']['subtitle'] if 'subtitle' in book['volumeInfo'] else None,
            'authors': ', '.join(book['volumeInfo']['authors']) if 'authors' in book['volumeInfo'] else None,
            'publisher': book['volumeInfo']['publisher'] if 'publisher' in book['volumeInfo'] else None,
            'published_date': book['volumeInfo']['publishedDate'] if 'publishedDate' in book['volumeInfo'] else None,
            'description': book['volumeInfo']['description'] if 'description' in book['volumeInfo'] else None,
            'categories': book['volumeInfo']['categories'] if 'categories' in book['volumeInfo'] else None,
        }
        table.upsert(book_info, keys=['book_id'])


def lambda_handler(event, context):
    start_year = 1800
    end_year = 1950
    books = search_books(start_year, end_year)
    store_books_in_db(books)
    return {
        'statusCode': 200,
        'body': json.dumps('Books stored in RDS database.')
    }



