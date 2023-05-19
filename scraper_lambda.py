import boto3
import dataset
import json
import requests

api_key = 'AIzaSyBgPYASTWnKJfz_eNzjuywNHMUt6cZV2xY' # Google Books API key
rds = boto3.client('rds')
db_rds = rds.describe_db_instances()['DBInstances'][0]
ENDPOINT = db_rds['Endpoint']['Address']
PORT = db_rds['Endpoint']['Port']
db_url = 'mysql+mysqlconnector://{}:{}@{}:{}/books'.format('username',
                                                           'password',
                                                           ENDPOINT,
                                                           PORT)
db = dataset.connect(db_url)


def search_books(subject, start_index):
    url = "https://www.googleapis.com/books/v1/volumes"
    parameters = {
        "q": "",
        "key": api_key,
        "printType": "books",
        "startIndex": start_index
    }
    books = []
    parameters["q"] = f"categories:{subject}"
    response = requests.get(url, params=parameters)
    if response.status_code == 200:
        results = json.loads(response.content)
        books.extend(results["items"])
    else:
        print(f"Failed to fetch results for subject {subject} at star index {start_index}.")

    
    return books


def store_books_in_db(books):
    ''' 
    Helper function to store all scraped books into db
    Input (list): information of all books from search_books function
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
        # book_id: unique identifier for a specific volume in Google Books API, like "9bnyDwAAQBAJ"
        table.upsert({'book_id': book['id'], 'book_info': json.dumps(book_info)}, ['book_id']) 


def lambda_handler(event, context):
    print('event is ', event)
    for batch in event['book']:
        subject = batch['subject']
        start_index = batch['start_index']

        books = search_books(subject, start_index)
        store_books_in_db(books)

    db.close()



