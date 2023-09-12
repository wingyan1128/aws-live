from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'company'


#if call / then will redirect to that pg

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('CompanyRegister.html')


@app.route("/about", methods=['POST'])
def about():
    return render_template('Login.html') 


@app.route("/companyReg", methods=['POST'])
def companyReg():
    company_name = request.form['company_name']
    email = request.form['email']
    contact = request.form['contact']
    address = request.form['address']
    type_of_business = request.form['type_of_business']
    num_of_employee = request.form['num_of_employee']
    overview = request.form['overview']
    password = request.form['password']

   
    insert_sql = "INSERT INTO company VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

     

    try:

        cursor.execute(insert_sql, (company_name, email, contact, address, type_of_business, num_of_employee, overview, password))
        db_conn.commit()
        

    except Exception as e:
        return str(e) 
        

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('CompanyLogin.html')



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
