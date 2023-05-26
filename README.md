# final-project-final_project_books
final-project-final_project_books created by GitHub Classroom

Group Member: Violet Huang, Ryan Liang, April Wang

Work Distribution
# 1. Scalable Data Scraping
1. Create an open source RDS database using ```'IpRanges': [{'CidrIp': '0.0.0.0/0'}]```
2. After creating a Google Cloud Account and a Google Cloud project specified by Google Books API, we can start our scraping process
3. Sppecifically, we perform a volumes search by sending an HTTP GET request to the following URI ```https://www.googleapis.com/books/v1/volumes?q=search+terms```
4. Our goal is to scrape social science related books, therefore we specify the following list of subjects as search terms:
    - [business, economics, environment, race, education, history, law, policy, politics, psychology, religion, society, communication, culture, fiction, textbook, crime]
5. This project aims to conduct a large scale scraping by parallelizing the searches, so we specify start index values. 
    - startIndex: The position in the collection at which to start. The index of the first item is 0. We use 800 as our range for startIndex.
    - maxResults: The maximum number of results to return. The default is 10, and the maximum allowable value is 40. We use 40 as our maxResults
6. In order to obtain the most representative datasets of social science related Google books, we roiginally wrote the lambda function [max_start.py](https://github.com/macs30123-s23/final-project-final_project_books/blob/main/max_start.py). This lambda function distributes across all subjects in our social science category, incrementing startIndex by 20 per request until run into either ```response_content.get('totalItems', 0) <= 0``` or ```response.status_code != 200``` However, by running the designed lambda function and distributing the tasks of finding individual max start index to different lambda worker, we keep hitting the maximum scraping limit returned by a status code of 429. Therefore, the issues of not being able to parallelize the tasks of finding the individual max start index is one of the limitation of our project
7. After manually checking for each category's max start index, we find the following corresponding max start index:
    - business: 900, economics: 880, environment: 960, race: 940, education: 960, history: 900, law: 940, policy: 960, politics: 960, psychology: 940, religion: 880, society: 960, communication: 960, culture: 960, fiction: 920, textbook: 940, crime: 940
    - Based on these maximum values, we have decided to set the uniform maximum start index to 800 for scraping books related to all categories. This choice ensures that a substantial number of books are retrieved for each category while also considering the variations in available books across different subjects.




# 2. Machine Learning

# 3. Natural Language Processing

# 4. Computer Vision
