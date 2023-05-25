"""
Author: Ryan Liang, Violet Huang
"""
import os
import boto3
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from pandas.io.json import json_normalize
import json

ENDPOINT = 'relational-db.cmzhp3dvx2ii.us-east-1.rds.amazonaws.com'
PORT = 3306
db_url = \
        'mysql+mysqlconnector://{}:{}@{}:{}/books'.format(
                                                'username',
                                                'password',
                                                ENDPOINT,
                                                PORT)

if __name__ == '__main__':
    engine = create_engine(db_url)

    # Read dataframe
    df = pd.read_sql_query("SELECT * FROM book_info", engine)

    # Transform columns
    df['book_info'] = df['book_info'].apply(json.loads)
    expanded_df = json_normalize(df['book_info'].tolist())
    expanded_df = expanded_df.drop(columns='book_id')
    final_df = df[['book_id']].join(expanded_df)

    # Convert columns to string
    cols_to_string = ['book_id', 'title', 'subtitle', 'authors', 'publisher', 'description', 'categories', 
                    'imageLinks.smallThumbnail', 'imageLinks.thumbnail']
    final_df[cols_to_string] = final_df[cols_to_string].astype(str)
    final_df['categories'] = final_df['categories'].str.replace("\\['", "").str.replace("\\']", "")

    # Extract year from 'published_date' and convert to int
    final_df['published_date'] = final_df['published_date'].str.extract('(\d{4})', expand=False).astype('Int64')

    # Drop empty column
    final_df = final_df.drop(columns='imageLinks')

    # Convert to Parquet
    final_df.to_parquet('book_info.parquet')