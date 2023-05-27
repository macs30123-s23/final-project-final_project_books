# final-project-final_project_books
The presentation slides are in the file [Final Presentation.pdf](https://github.com/macs30123-s23/final-project-final_project_books/blob/main/Final%20Presentation.pdf).

Group Member: Violet Huang, Ryan Liang, April Wang

# Social Significance:
The task of scraping social science related books using the Google Books API carries social significance and presents valuable opportunities for information mining. By accessing and analyzing a vast collection of books using large scale method, we can explore valuable insights and trends in social science topics acorss years and genres. Through sentiment analysis, we have gained a deeper understanding of the prevailing sentiments, attitudes, and perspectives expressed within these books based on scraped description attributed to the book, shedding light on societal attitudes and opinions on social science issues. Furthermore, employing machine learning techniques for categorization and topic modeling, we extracted insightful thematic information from the data, identifying key themes, trends, and patterns in social science literature. This information can be utilized to inform policy-making, academic research, and social discourse, providing a comprehensive and data-driven understanding of various social science domains. The availability of this vast collection of books through the Google Books API opens up new possibilities for data-driven research and enriches our understanding of the social world.


# Work Distribution
- April Wang: Collected data using Google Books API, parallelized with AWS lambda function and step function, stored book information in AWS RDS table
- Violet Huang: Cleaned Data, performed supervised machine learning prediction task, generate Roberta sentence embedding
- Ryan Liang: Cleaned Data, employed natural language processing with BERT topic, applied computer vision with Google Cloud API to book cover

# 1. Scalable Data Scraping
The lambda function can be found [here](https://github.com/macs30123-s23/final-project-final_project_books/blob/main/scraper_lambda.py) and the jupyter notebook on scraping can be found [here](https://github.com/macs30123-s23/final-project-final_project_books/blob/main/scrape_book.ipynb)
1. Create an open source RDS database using ```'IpRanges': [{'CidrIp': '0.0.0.0/0'}]```
2. After creating a Google Cloud Account and a Google Cloud project specified by Google Books API, we can start our scraping process
3. Sppecifically, we perform a volumes search by sending an HTTP GET request to the following URI ```https://www.googleapis.com/books/v1/volumes?q=search+terms```
4. Our goal is to scrape social science related books, therefore we specify the following list of subjects as search terms:
    - cat_lst = ['business', 'economics', 'environment', 'race', 'education', 'history', 'law', 'policy', 'politics', 'psychology', 'religion', 'society', 'communication', 'culture', 'fiction', 'textbook', 'crime']
5. This project aims to conduct a large scale scraping by parallelizing the searches, so we specify start index values. 
    - startIndex: The position in the collection at which to start. The index of the first item is 0. We use 800 as our range for startIndex.
    - maxResults: The maximum number of results to return. The default is 10, and the maximum allowable value is 40. We use 40 as our maxResults
6. In order to obtain the most representative datasets of social science related Google books, we roiginally wrote the lambda function [max_start.py](https://github.com/macs30123-s23/final-project-final_project_books/blob/main/max_start.py). This lambda function distributes across all subjects in our social science category, incrementing startIndex by 20 per request until run into either ```response_content.get('totalItems', 0) <= 0``` or ```response.status_code != 200``` However, by running the designed lambda function and distributing the tasks of finding individual max start index to different lambda worker, we keep hitting the maximum scraping limit returned by a status code of 429. Therefore, the issues of not being able to parallelize the tasks of finding the individual max start index is one of the limitation of our project
7. After manually checking for each category's max start index, we find the following corresponding max start index:
    - business: 900, economics: 880, environment: 960, race: 940, education: 960, history: 900, law: 940, policy: 960, politics: 960, psychology: 940, religion: 880, society: 960, communication: 960, culture: 960, fiction: 920, textbook: 940, crime: 940
    - Based on these maximum values, we have decided to set the uniform maximum start index to 800 for scraping books related to all categories. This choice ensures that a substantial number of books are retrieved for each category while also considering the variations in available books across different subjects.
8. Based on above justification, we created a set of start index using the following codes:
```
start_indices = list(range(0, 840, 40))
batches = []
for cat in cat_lst:
    for start_index in start_indices:
        batches.append({'book':[cat, start_index]})
```
such that we obtain the following batch: [{'book': ['business', 0]}, {'book': ['business', 40]}, {'book': ['business', 80]}, ...,  {'book': ['crime', 720]},
 {'book': ['crime', 800]}]
9. Finally, we formulate the following lambda function using similar logic in assignment 2 to distribute the scraping task into two fold paralleling
        - Distribute the tasks of collecting social science related books to each lambda in charge of only one category
        - Further distribute the task of collecting books of a specific category into subtask, such that each lambda worker scrape information on 40 books on this category

```
def search_books(subject, start_index):
    url = "https://www.googleapis.com/books/v1/volumes"
    parameters = {
        "q": subject,
        "key": api_key,
        "printType": "books",
        "maxResults": 40,
        "startIndex": start_index
    }
    books = []
    while True:
        try:
            response = requests.get(url, params=parameters)
            break
        except:
            continue
    if response.status_code == 200:
        results = json.loads(response.content)
        books.extend(results["items"])
    else:
        print(response)
        print(f"Failed to fetch results for subject {subject} at start index {start_index}.")
    return books
```

```
def store_books_in_db(books):
    ''' 
    Helper function to store all scraped books into db
    Input (list): information of all books from search_books function
    '''

    table = db['book_info2']

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
            'imageLinks': book['volumeInfo']['imageLinks'] if 'imageLinks' in book['volumeInfo'] else None
        }

        existing_book = table.find_one(book_id=book['id'])
        if not existing_book:
            table.upsert({'book_id': book['id'], 'book_info2': json.dumps(book_info)}, ['book_id']) 
```

```
def lambda_handler(event, context):
    books_batches = event['book']
    subject = books_batches[0]
    start_index = books_batches[1]
    books = search_books(subject, start_index)
    store_books_in_db(books)
```



# 2. Multiclass Prediction 
This part of the project is focused on predicting the category of a book based on its description using machine learning techniques. It utilizes the dataset mentioned, and employs a Natural Language Processing (NLP) pipeline in conjunction with logistic regression for the text classification task.

The dataset is first processed to create a balanced distribution for each category. Categories with less than 100 books are discarded. The remaining categories are then down-sampled or upsampled to create a dataset with 300 books for each category. Categories include: Medical, Religion, Psychology, Political Science, Social Science, Science, Literary Criticism, Education, Fiction, History, Law, Language Arts & Disciplines, Philosophy, Biography & Autobiography, Business & Economics

The NLP pipeline consists of several steps:

1. Document assembly: converting raw input into usable text data
2. Tokenization: breaking down the text into individual words (tokens)
3. Stopword removal: eliminating common words that don't provide valuable information
4. Lemmatization: reducing words to their base or root form (e.g., "running" to "run")
5, Count Vectorization: converting the processed text data into a numerical representation that machine learning algorithms can understand

The processed data is then fed into a logistic regression model, a common method for text classification tasks. The model is trained to predict the book category based on the processed description. The most predictive words for each category are extracted from the model, providing insight into the words that heavily influence the classification into each category.

This project showcases the power and scalability of Apache Spark in handling large-scale text data and implementing machine learning algorithms efficiently. The script uses PySpark, a Python library for Spark programming, to build and run the NLP pipeline and logistic regression model.

The output of this project includes the logistic regression model and a list of the most predictive words for each category. These words are presented along with their coefficients, which represent their influence on the prediction of each category.

This project could be of particular interest to researchers, data scientists, or businesses in the publishing industry seeking to understand and predict book categories based on descriptions, or to anyone interested in text classification and natural language processing.

# 3. Natural Language Processing
The purpose of this step is to use the BERTopic (https://github.com/MaartenGr/BERTopic) as the method to explore the topics in the  in unsupervised scheme. Compared with the original BERTopic implementation, my implementation 

A common BERTopic workflow consists of these three steps:
- Transfer learning with BERT-class models to generate (sentence) embeddings for each entry of corpus.
- Dimension Reduction of the embedding vectors with PCA, t-SNE or UMAP to prepare for clustering.
- Clustering with algorithms as K-Means, DBSCAN, HDBSCAN depending on the research purpose. For this project, I choose to use hierarchical clustering algorithm, as I want low tolerance of meaningless clusters.

The common bottleneck of BERTopic in my experience is in the steps of dimension reduction (often with UMAP), and clustering (hierarchical clustering with HDBSCAN in the use case of this project). When the size data entries is large (>100K), with the large size of dimensions of input embedding vectors (512), computation time of these two steps deteriorate. That was because in the original code, these vector calculations are serialized.

Therefore, for these free steps, I deploy different strategies to speedup with scalable operations:
 - Transfer learning embedding generation with SparkNLP
 - Dimension reduction and hierarchical clustering with GPU speedup with cuML, as they are vector calculations.

The code workflow and the results are shown in the notebook [BERTopic with SparkML and cuML.ipynb](https://github.com/macs30123-s23/final-project-final_project_books/blob/main/BERTopic%20with%20SparkML%20and%20cuML.ipynb). As the result, the HDBSCAN clustering generated 8 valid clusters for 3K entries in the valid size of data entries of 7K, which is a nature of hierarchical clustering. The clustering results are presented by the ranking if "important words" in the clusters with the highest TF-IDF scores.

# 4. Computer Vision
The code of this step is in [Google Vision API Cover  Analysis.ipynb](https://github.com/macs30123-s23/final-project-final_project_books/blob/main/Google%20Vision%20API%20Cover%20%20Analysis.ipynb). This step we did a computer vision analysis on the covers of the book metadata with Google Cloud Vision API. With the API call of [AnnotateImageRequest](https://cloud.google.com/vision/docs/reference/rest/v1/AnnotateImageRequest), we can have a list of the recognized objects within the book cover by the cloud-based image recognition model. This step is parallelized by AWS Lambda function. Corresponding Lambda function code is in the file of [google_vision_lambda.py](https://github.com/macs30123-s23/final-project-final_project_books/blob/main/google_vision_lambda.py).

In order to analyze the design patterns over the social science literatures, we can use a different way to interpret the visual elements. We can interpret the cover as a "documents" that are consisted of design elements as "words". In this way, we can perform an LDA analysis, to explore what are the clusters of design patterns over our scraped books. I filter the design elements that exists over 80% of books or with frequency less than 2. The number of LDA topics is set at 10 for convenience. The LDA is parallelized with multicore with the python package gensim, and its topic modelling results are shown in the notebook.

The interactive pattern analysis LDA is provided in the file of [Google Vision API Cover  Analysis.html](https://github.com/macs30123-s23/final-project-final_project_books/blob/main/Google%20Vision%20API%20Cover%20%20Analysis.html).
