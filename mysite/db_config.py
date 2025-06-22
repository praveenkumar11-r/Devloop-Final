import mysql.connector

def connect_db():
    return mysql.connector.connect(
        host='245124735122.mysql.pythonanywhere-services.com',
        user='245124735122',
        password='kingsman64k',
        database='245124735122$task_manager'
    )
