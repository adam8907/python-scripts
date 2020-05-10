#!/usr/bin/python3
####################################
#                                  #
# Created by: Adamski Molina       #
# Email: adamski.molina@f5.com>    #
# Version: 1                       #
#                                  #
####################################
import sqlite3
from sqlite3 import Error
from prettytable import PrettyTable

def db_conn(db_file):

  conn = ""
  try:
      conn = sqlite3.connect(db_file)
  except Error as e:
      print (e)
  return conn

def query_table(query):
    db_name = "demo.db"
    conn = db_conn(db_name)
    cursor = conn.cursor()
    cursor.execute(query_id)
    data = cursor.fetchall()
    table = PrettyTable()
    table.field_names = ["Day", "No. Casos", "Team"]

query = "select date_assig, count(*), team from cases where date_assig LIKE '%Abr%' group by date_assig,team"
query_table(query)