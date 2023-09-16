from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from botocore.exceptions import ClientError
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
s3=boto3.client('s3')


#if call / then will redirect to that pg

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('Home.html')


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

        cursor.execute(insert_sql, (companyName, companyEmail, companyContact, companyAddress, typeOfBusiness, numOfEmployee, overview, companyPassword, status,))
        db_conn.commit()
        

    except Exception as e:
        return str(e) 
        

    finally:
        cursor.close()

    return render_template('CompanyRegister.html', registerSuccessful=True)


@app.route("/companyLogin", methods=['GET','POST'])
def companyLogin():
    companyEmail = request.form['companyEmail']
    companyPassword = request.form['companyPassword']
    company_filename_in_s3 = str(companyEmail) + "_file.pdf"
    expiration = 3600
    
    fetch_company_sql = "SELECT * FROM company WHERE companyEmail = %s"
    cursor = db_conn.cursor()

    if companyEmail == "" and companyPassword == "":
        return render_template('CompanyLogin.html', empty_field=True)

    try:
        cursor.execute(fetch_company_sql, (companyEmail))
        companyRecord = cursor.fetchone()

        if not companyRecord:
            return render_template('CompanyLogin.html', no_record=True)

        if companyRecord[8] != "Approved":
            return render_template('CompanyLogin.html', not_Approved=True)

        if companyRecord[7] != companyPassword:
            return render_template('CompanyLogin.html', login_failed=True)
        else:
            try:
                response = s3.generate_presigned_url('get_object',
                                                    Params={'Bucket': custombucket,
                                                            'Key': company_filename_in_s3},
                                                    ExpiresIn=expiration)
            except ClientError as e:
                logging.error(e)

            if response is None:
                return render_template('CompanyPage.html', company = companyRecord, file_exist = False)
            else:
                return render_template('CompanyPage.html', company = companyRecord, file_exist = True, url = response)

    except Exception as e:
        return str(e)

    finally:
        cursor.close()

@app.route("/companyUpload", methods=['POST'])
def companyUpload():
    companyEmail = request.form['companyEmail']
    company_File = request.files['company_File']
    company_filename_in_s3 = str(companyEmail) + "_file.pdf"
    
    fetch_company_sql = "SELECT * FROM company WHERE companyEmail = %s"
    cursor = db_conn.cursor()
    
    try:
        expiration = 3600

        # Check if a file has been uploaded
        if company_File.filename == "":
            return render_template('CompanyPage.html', company=companyRecord, no_file_uploaded=True, file_exist=False)

        # Generate a pre-signed URL to check if the file exists
        try:
            response = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': custombucket, 'Key': company_filename_in_s3},
                ExpiresIn=expiration
            )
        except ClientError as e:
            logging.error(e)

        cursor.execute(fetch_company_sql, (companyEmail))
        companyRecord = cursor.fetchone()

        # Check if the response is None, indicating the file doesn't exist
        if response is None:
            return render_template('CompanyPage.html', company=companyRecord, file_exist=False)

        # Handle the case where a file exists
        # Upload the file to S3 here if needed

        # Generate another pre-signed URL for downloading
        try:
            response = s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': custombucket, 'Key': company_filename_in_s3},
                ExpiresIn=expiration
            )
        except ClientError as e:
            logging.error(e)

        return render_template('CompanyPage.html', company=companyRecord, file_exist=True, url=response)
        
    except Exception as e:
        return str(e)

    finally:
        cursor.close()

@app.route("/studViewCompany")
def studViewCompany():
    status = "Approved"

    fetch_company_sql = "SELECT * FROM company WHERE status = %s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(fetch_company_sql, (status))
        companyRecords = cursor.fetchall()
    
        return render_template('StudViewCompany.html', company=companyRecords)    

    except Exception as e:
        return str(e)      

    finally:
        cursor.close()


@app.route("/studRegister", methods=['POST'])
def studRegister():
    cohort = request.form['cohort']
    internPeriod = request.form['internPeriod']
    studName = request.form['studName']
    studId = request.form['studId']
    studIc = request.form['studIc']
    studGender = request.form['studGender']
    programme = request.form['programme']
    studEmail = request.form['studEmail']
    studContact = request.form['studContact']
    uniSupervisor = request.form['uniSupervisor']
    uniEmail = request.form['uniEmail']
    companyName = ""
    monthlyAllowance = ""
    companySvName = ""
    companySvEmail = ""

   
    insert_sql = "INSERT INTO student VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

     

    try:

        cursor.execute(insert_sql, (cohort, internPeriod, studName, studId, studIc, studGender, programme, studEmail, studContact, uniSupervisor, uniEmail
                                   ,companyName ,monthlyAllowance ,companySvName, companySvEmail))
        db_conn.commit()
        

    except Exception as e:
        return str(e) 
        

    finally:
        cursor.close()

    return render_template('StudLogin.html', studRegisterSuccessfully = True)


@app.route("/studLogin", methods=['GET', 'POST'])
def studLogin():
    studEmail = request.form['studEmail']
    studIc = request.form['studIc']
    #status = "Pending Approval"


    fetch_student_sql = "SELECT * FROM student WHERE studEmail = %s"
    #fetch_company_sql = "SELECT * FROM company WHERE status = %s"
    cursor = db_conn.cursor()

    
    if studEmail == "" and studIc == "":
        return render_template('StudLogin.html', empty_field=True)

    try:
        cursor.execute(fetch_student_sql, (studEmail))
        records = cursor.fetchall()

        # cursor.execute(fetch_company_sql, (status))
        # companyRecords = cursor.fetchall()

        if not records:
            return render_template('StudLogin.html', login_failed=True)

        if records and records[0][4] != studIc:
            return render_template('StudLogin.html', login_failed=True)
        else:
            return render_template('StudPage.html', student=records)

    except Exception as e:
        return str(e)

    finally:
        cursor.close()


@app.route("/studPage", methods=['GET','POST'])
def studPage():
    # cohort = request.form['cohort']
    # internPeriod = request.form['internPeriod']
    # studName = request.form['studName']
    # studId = request.form['studId']
    # studIc = request.form['studIc']
    # studGender = request.form['studGender']
    # programme = request.form['programme']
    #studEmail = request.form['studEmail']
    # studContact = request.form['studContact']
    # uniSupervisor = request.form['uniSupervisor']
    # uniEmail = request.form['uniEmail']
    companyName = request.form['companyName']
    companyAllowance = request.form['companyAllowance']
    companySvName = request.form['companySvName']
    companySvEmail = request.form['companySvEmail']
    studId = request.args.get('studId')
    companyApForm = request.files['companyApForm']
    parentAckForm = request.files['parentAckForm']
    letterOIdt = request.files['letterOIdt']
    hiredEvid = request.files['hiredEvid']
    

    #fetch_student_sql = "SELECT * FROM student WHERE studId = %s"
    sql = "UPDATE student SET companyName = %s AND companyAllowance = %s AND companySvName = %s AND companySvEmail = %s WHERE studId = %s"
    cursor = db_conn.cursor()

    try:
        # cursor.execute(fetch_student_sql, (studId))
        # records = cursor.fetchall()

        # if records == "":
        #     return render_template('studPage.html', invalid_error=True)
        cursor.execute(sql, (companyName, companyAllowance,companySvName, companySvEmail, studId,))
        db_conn.commit()
       
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "stud-id-" + str(studId) + "_file.pnf"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading files to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=companyApForm)
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=parentAckForm)
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=letterOIdt)
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=hiredEvid)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)
       
    finally:
        cursor.close()

    print("all modification done...")
    return render_template('StudPage.html')


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
        cursor.execute(fetch_admin_sql, (adminEmail,))
        records = cursor.fetchall()

        cursor.execute(fetch_company_sql, (status,))
        companyRecords = cursor.fetchall()

        if not records:
            return render_template('AdminLogin.html', login_failed=True)
        if records and records[0][2] != adminPassword:
            return render_template('AdminLogin.html', login_failed=True)
        else:
            return render_template('AdminPage.html', admin=records, company=companyRecords)

    except Exception as e:
        return str(e)

    finally:
        cursor.close()


@app.route("/approveCompany", methods=['GET', 'POST'])
def approveCompany():

    status="Approved"
    status2="Pending Approval"
    companyName = request.args.get('companyName')
    adminEmail = request.args.get('adminEmail')

    fetch_admin_sql = "SELECT * FROM admin WHERE adminEmail = %s"
    fetch_company_sql = "SELECT * FROM company WHERE status = %s"
    sql = "UPDATE company SET status = %s WHERE companyName = %s"
    cursor = db_conn.cursor()

  
    try:
        cursor.execute(fetch_admin_sql, (adminEmail,))
        records = cursor.fetchall()
        
        cursor.execute(sql, (status, companyName,))
        db_conn.commit()

        cursor.execute(fetch_company_sql, (status2,))
        companyRecords = cursor.fetchall()


        return render_template('AdminPage.html', admin=records, company=companyRecords, updateSuccessful=True )

    except Exception as e:
        return str(e)

    finally:
        cursor.close()

@app.route("/rejectCompany", methods=['GET', 'POST'])
def rejectCompany():

    status="Rejected"
    status2="Pending Approval"
    companyName = request.args.get('companyName')
    adminEmail = request.args.get('adminEmail')

    fetch_admin_sql = "SELECT * FROM admin WHERE adminEmail = %s"
    fetch_company_sql = "SELECT * FROM company WHERE status = %s"
    sql = "UPDATE company SET status = %s WHERE companyName = %s"
    cursor = db_conn.cursor()

  
    try:
        cursor.execute(fetch_admin_sql, (adminEmail,))
        records = cursor.fetchall()
        
        cursor.execute(sql, (status, companyName,))
        db_conn.commit()

        cursor.execute(fetch_company_sql, (status2,))
        companyRecords = cursor.fetchall()


        return render_template('AdminPage.html', admin=records, company=companyRecords, updateSuccessful=True )

    except Exception as e:
        return str(e)

    finally:
        cursor.close()

@app.route("/toAdminLogin")
def toAdminLogin():
    return render_template('AdminLogin.html') 

@app.route("/toCompanyLogin")
def toCompanyLogin():
    return render_template('CompanyLogin.html') 

@app.route("/toCompanyRegister")
def toCompanyRegister():
    return render_template('CompanyRegister.html') 

@app.route("/toStudRegister")
def toStudRegister():
    return render_template('StudRegister.html') 

@app.route("/toStudLogin")
def toStudLogin():
    return render_template('StudLogin.html') 





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
