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
    return render_template('AdminLogin.html')


@app.route("/companyLogin")
def companyLogin():
    return render_template('CompanyLogin.html') 


@app.route("/companyReg", methods=['POST'])
def companyReg():
    companyName = request.form['companyName']
    companyEmail = request.form['companyEmail']
    companyContact = request.form['companyContact']
    companyAddress = request.form['companyAddress']
    typeOfBusiness = request.form['typeOfBusiness']
    numOfEmployee = request.form['numOfEmployee']
    overview = request.form['overview']
    companyPassword = request.form['companyPassword']
    status = "Pending Approval"

   
    insert_sql = "INSERT INTO company VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

     

    try:

        cursor.execute(insert_sql, (companyName, companyEmail, companyContact, companyAddress, typeOfBusiness, numOfEmployee, overview, companyPassword, status))
        db_conn.commit()
        

    except Exception as e:
        return str(e) 
        

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('CompanyLogin.html')


@app.route("/adminLogin", methods=['GET', 'POST'])
def adminLogin():
    adminEmail = request.form['adminEmail']
    adminPassword = request.form['adminPassword']
    status = "Pending Approval"


    
    fetch_admin_sql = "SELECT * FROM admin WHERE adminEmail = %s"
    fetch_company_sql = "SELECT * FROM company WHERE status = %s"
    cursor = db_conn.cursor()

    if adminEmail == "" and adminPassword == "":
        return render_template('AdminLogin.html', empty_field=True)

    try:
        cursor.execute(fetch_admin_sql, (adminEmail))
        records = cursor.fetchall()

        cursor.execute(fetch_company_sql, (status))
        companyRecords = cursor.fetchall()

        if records and records[0][2] != adminPassword:
            return render_template('AdminLogin.html', login_failed=True)
        else:
            return render_template('AdminPage.html', admin=records, company=companyRecords)

    except Exception as e:
        return str(e)

    finally:
        cursor.close()

    


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
