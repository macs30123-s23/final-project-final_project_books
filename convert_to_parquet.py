"""
Author: Ryan Liang
"""
import os
import boto3
import numpy as np
import pandas as pd
import mysql.connector

ENDPOINT = 'relational-db.cmzhp3dvx2ii.us-east-1.rds.amazonaws.com'
PORT = 3306

if __name__ == '__main__':
    conn =  mysql.connector.connect(host=ENDPOINT,
                                user="username",
                                passwd="password", 
                                port=PORT, 
                                database='books')
    cur = conn.cursor()
    cur.execute("SELECT * FROM book_info")
    rows = cur.fetchall()
    column_names = [i[0] for i in cur.description]
    df = pd.DataFrame(rows, columns=column_names)
    df.to_parquet('book_info.parquet')