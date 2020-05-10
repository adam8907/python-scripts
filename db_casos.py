#!/usr/bin/python3
####################################
#                                  #
# Created by: Adamski Molina       #
# Email: adamski.molina@f5.com>    #
# Version: 1                       #
#                                  #
####################################
import sqlite3
import xlrd
import string
from sqlite3 import Error
import re

def db_conn(db_file):

  conn = ""
  try:
      conn = sqlite3.connect(db_file)
  except Error as e:
      print (e)
  return conn

def get_eng_available(sheet):
    sheet  = sheet
    n_eng = 0
    for i in range (1,sheet.nrows):
        if sheet.cell_value(i,3) == 'y' or sheet.cell_value(i,3) == 'Y':
            n_eng += 1
    return n_eng

def reading_excel(file_name, sheet_name, index_sheet):
    # Getting data
    n_eng = 0
    location = file_name
    wb = xlrd.open_workbook(location)
    sheet_name = wb.sheet_names()[index_sheet]
    sheet_temp = sheet_name.split(" ")
    if sheet_temp[0] == "APR":
        if sheet_temp[1][0] == '0':
           sheet_temp[1] = sheet_temp[1][1]
        sheet_name = sheet_temp[0].replace("APR", "Abril " + sheet_temp[1])
    print (sheet_name)
    
    sheet = wb.sheet_by_index(index_sheet)
    n_eng = get_eng_available(sheet)
    
    for i in range (1,sheet.nrows):
        cell = []
        col_type = sheet.cell_type(i, 2)
        #print (sheet.cell_value(i,2))
        #Checking that the cell is not empty
        if col_type == xlrd.XL_CELL_EMPTY:
            return 
        for j in range (2,sheet.ncols):
            #Check the type of a cel
            col_type = sheet.cell_type(i, j)
            #Checking that the cell is not empty
            if not col_type == xlrd.XL_CELL_EMPTY and sheet.cell_value(i,j) != "N/A":
                if col_type == 2:
                    print ("Converting data")
                    cell_type = int (sheet.cell_value(i,j))
                    cell.append(str(cell_type))
                else:
                    cell.append(str(sheet.cell_value(i,j)))
        #print (cell)        
        parse_case(cell, sheet_name, file_name,n_eng)
        

def parse_case(data, sheet_name, team,n_eng):
    list_cell = data
    n_eng = n_eng
    case = []
    #Getting casos
    team = team[0:4]

    for i in range(len(list_cell)):
        case_rg = re.findall("^C[0-9]+[0-9]$", str(list_cell[i].strip()))
        case_rg_1 = re.findall("^[0-9]-[0-9]+$", str(list_cell[i].strip()))
        
        if case_rg !=[] or case_rg_1 !=[]:
            case.append (list_cell[0])
            case.append(list_cell[i])
            case.append(list_cell[i+1])
            case.append(list_cell[i+2])
            i += 3
            insert_data_db(case, sheet_name,team, n_eng)
        else:
            case = []
            i += 1


def insert_data_db(data, sheet_name,team, n_eng):
    list_cell = data
    print (data)
    n_eng = n_eng
    db_name = "demo.db"
    conn = db_conn(db_name)
    cursor = conn.cursor()
    #Getting the user ID
    user = list_cell[0].strip().replace(" ",",")
    query_id = "SELECT user_id FROM users WHERE name LIKE " + "'%" + user.strip().split(",")[-1] + "%'"
    query_module = "SELECT mod_id FROM modules WHERE name LIKE " + "'%" + list_cell[2].strip() + "%'"
    #print (query_module)
    cursor.execute(query_id)
    user_id = cursor.fetchall()
    cursor.execute(query_module)
    module_id = cursor.fetchall()
    #Inserting data to the DB
    query = """INSERT INTO cases (n_case, mod_id, user_id, severity, date_assig, team, n_eng) VALUES ('""" + list_cell[1].strip() + """',""" + str(module_id[0][0]) + """,""" + str(user_id[0][0]) +""",""" + str(list_cell[3]).strip() + """,'""" + sheet_name + """','""" + team + """','""" + str(n_eng) + """')"""
    print (query)
    cursor.execute(query)
    conn.commit()
    conn.close()
    

def check_sheet_name(sheet_name, file_name):
    #Verify if the file was already read
    team = file_name[0:4]
    conn = db_conn(db_name)
    cursor = conn.cursor()
    query = "SELECT date_assig FROM cases WHERE date_assig='" + sheet_name +"' and team='" + team + "'"
    cursor.execute(query)
    sheet = cursor.fetchall()
    if sheet == []:
        return True
    return False

##### Connecting to the DB

db_name = "demo.db"
file_name = "NA19-SR-Distribution.xlsx"
conn = db_conn(db_name)
wb = xlrd.open_workbook(file_name)
sheet_names = wb.sheet_names()
i = 0
for sheet in sheet_names:
    if check_sheet_name(sheet,file_name) and sheet != "Master" and "Abril" in sheet:
       reading_excel(file_name, sheet, i)
    i += 1



