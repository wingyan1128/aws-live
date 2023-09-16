from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from botocore.exceptions import ClientError
from botocore.exceptions import NoCredentialsError
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
s4 = boto3.client('s3')


#if call / then will redirect to that pg

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('Home.html')

@app.route("/svLogin", methods=['GET', 'POST'])
def svLogin():
    svEmail = request.form['svEmail']
    svPassword = request.form['svPassword']

    fetch_supervisor_sql = "SELECT * FROM supervisor WHERE svEmail = %s"
    fetch_student_sql = "SELECT * FROM student WHERE uniEmail = %s"

    cursor = db_conn.cursor()

    try:
        if not svEmail or not svPassword:
            return render_template('StaffLogin.html', empty_field=True)

        cursor.execute(fetch_supervisor_sql, (svEmail,))
        supervisor_records = cursor.fetchall()

        if not supervisor_records:
            return render_template('StaffLogin.html', login_failed=True)

        elif supervisor_records and supervisor_records[0][6] != svPassword:
            return render_template('StaffLogin.html', login_failed=True)

        cursor.execute(fetch_student_sql, (svEmail,))
        student_records = cursor.fetchall()

        # Generate URLs for student files from S3
        student_records_urls = []
        file_names = ["file1", "file2", "file3", "file4"]
        expiration = 3600

        for student in student_records:
            student_id = student[1]
            student_urls = []
            object_prefix = str(student_id)
            
            # assuming the files are saved in this form at student page
            # eg/ 21WMR01091_com_acceptance_form.pdf
            #file1 = "stud-id-" + str(studId) + "_file1.pdf"
            
            for file_name in file_names:
                object_key = "stud-id-" + str(object_prefix) + "_" + str(file_name) + ".pdf"
               
                try:
                # Check if the file exists in S3
                    s3.head_object(Bucket=custombucket, Key=object_key)

                # If the file exists, generate a presigned URL
                    response = s3.generate_presigned_url(
                        'get_object',
                        Params={
                            'Bucket': custombucket,
                            'Key': object_key
                        },
                        ExpiresIn=expiration
                    )
                    student_urls.append(response)  # Add the URL to the student's URL list

                except NoCredentialsError:
                    return "AWS credentials not available."
                except s3.exceptions.NoSuchKey:
                    # The file doesn't exist, you can handle this case if needed
                    response = "none"
                    student_urls.append(response)
                except ClientError as e:
                    if e.response['Error']['Code'] == '404':
                        response = "none"
                        student_urls.append(response)

            print(student_urls)

            # Check if student_urls has at least 3 elements before appending to student_records_urls
            if len(student_urls) >= 3:
                student_records_urls.append(student_urls)  # Add the student's URL list to the 2D table
            else:
            # Handle the case where there are not enough elements in student_urls
                student_records_urls.append(["none"] * len(file_names))  # Add "none" for missing URLs
            
        return render_template('StaffPage.html', supervisor=supervisor_records[0], students=student_records, urls=student_records_urls)
    except Exception as e:
        app.logger.error(str(e))
        return "An error occurred."
    finally:
        cursor.close()

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
        elif companyRecord[8] != "Approved":
            return render_template('CompanyLogin.html', not_Approved=True)
        elif companyRecord[7] != companyPassword:
            return render_template('CompanyLogin.html', login_failed=True)
        else:
            # Check if the file exists in the S3 bucket
            try:
                s3.head_object(Bucket=custombucket, Key=company_filename_in_s3)
                file_exists = True
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    file_exists = False
                else:
                    logging.error(e)
                    return str(e)

            if not file_exists:
                return render_template('CompanyPage.html', company=companyRecord, file_exist=False)
        
        # Generate a pre-signed URL for downloading the file
            try:
                response = s3.generate_presigned_url('get_object',
                                                Params={'Bucket': custombucket,
                                                        'Key': company_filename_in_s3},
                                                ExpiresIn=expiration)
            except ClientError as e:
                logging.error(e)

            return render_template('CompanyPage.html', company=companyRecord, file_exist=True, url=response)

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
        try:
            response = s3.generate_presigned_url('get_object',
                                                Params={'Bucket': custombucket,
                                                        'Key': company_filename_in_s3},
                                                ExpiresIn=expiration)
        except ClientError as e:
            logging.error(e)
        cursor.execute(fetch_company_sql, (companyEmail))
        companyRecord = cursor.fetchone()

        if company_File.filename == "":
            if response is None:
                return render_template('CompanyPage.html', company=companyRecord, no_file_uploaded=True, file_exist = False)
            else:
                return render_template('CompanyPage.html', company=companyRecord, file_exist = True, url = response, no_file_uploaded=True)
        else:
            upload = boto3.resource('s3')
            upload.Bucket(custombucket).put_object(Key=company_filename_in_s3, Body=company_File)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            upload_location = (bucket_location['LocationConstraint'])

            if upload_location is None:
                upload_location = ''
            else:
                upload_location = '-' + upload_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                upload_location,
                custombucket,
                company_filename_in_s3)

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

@app.route("/studViewCompany")
def studViewCompany():
    status = "Approved"
    studEmail = request.args.get('studEmail')

    fetch_company_sql = "SELECT * FROM company WHERE status = %s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(fetch_company_sql, (status))
        companyRecords = cursor.fetchall()
    
        return render_template('StudViewCompany.html', company=companyRecords, studEmail=studEmail)    

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
    cursor = db_conn.cursor()

    if studEmail == "" and studIc == "":
        return render_template('StudLogin.html', empty_field=True)

    try:
        cursor.execute(fetch_student_sql, (studEmail))
        records = cursor.fetchall()

        # cursor.execute(fetch_company_sql, (status))
        # companyRecords = cursor.fetchall()

        if not records:
            return render_template('StudLogin.html', not_exist=True)
        elif records[0][4] != studIc:
            return render_template('StudLogin.html', login_failed=True)
        else:
            return render_template('StudPage.html', student=records)

    except Exception as e:
        return str(e)

    finally:
        cursor.close()


@app.route("/studPage", methods=['POST'])
def studPage():

    companyName = request.form['companyName']
    monthlyAllowance = request.form['monthlyAllowance']
    companySvName = request.form['companySvName']
    companySvEmail = request.form['companySvEmail']
    studId = request.form['studId']
    companyApForm = request.files['companyApForm']
    parentAckForm = request.files['parentAckForm']
    letterOIdt = request.files['letterOIdt']
    hiredEvid = request.files['hiredEvid']
    expiration = 3600
    
    sql = "UPDATE student SET companyName = %s, monthlyAllowance = %s, companySvName = %s, companySvEmail = %s WHERE studId = %s"
    fetch_student_sql = "SELECT * FROM student WHERE studId = %s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(sql, (companyName, monthlyAllowance, companySvName, companySvEmail, studId))
        cursor.execute(fetch_student_sql, (studId))
        records = cursor.fetchall()
        db_conn.commit()
        
        # Uplaod image file in S3 #
        file1 = "stud-id-" + str(studId) + "_file1.pdf"
        file2 = "stud-id-" + str(studId) + "_file2.pdf"
        file3 = "stud-id-" + str(studId) + "_file3.pdf"
        file4 = "stud-id-" + str(studId) + "_file4.pdf"
        s3 = boto3.resource('s3')

        try:
            
            if companyApForm.filename !="" and parentAckForm.filename !="" and letterOIdt.filename !="" and hiredEvid.filename !="":
                s3.Bucket(custombucket).put_object(Key=file1, Body=companyApForm)
                s3.Bucket(custombucket).put_object(Key=file2, Body=parentAckForm)
                s3.Bucket(custombucket).put_object(Key=file3, Body=letterOIdt)
                s3.Bucket(custombucket).put_object(Key=file4, Body=hiredEvid)
            else:
                 return render_template('StudPage.html', files_empty=True)

            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                file1)
            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                file2)
            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                file3)
            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                file4)

        
            response1 = s4.generate_presigned_url('get_object',
                                                Params={'Bucket': custombucket,
                                                        'Key': file1},
                                                ExpiresIn=expiration)
            response2 = s4.generate_presigned_url('get_object',
                                                Params={'Bucket': custombucket,
                                                        'Key': file2},
                                                ExpiresIn=expiration)
            response3 = s4.generate_presigned_url('get_object',
                                                Params={'Bucket': custombucket,
                                                        'Key': file3},
                                                ExpiresIn=expiration)
            response4 = s4.generate_presigned_url('get_object',
                                                Params={'Bucket': custombucket,
                                                        'Key': file4},
                                                ExpiresIn=expiration)

        except Exception as e:
                return str(e)

    finally:
        cursor.close()

    return render_template('StudPageOutput.html', student = records, url1=response1, url2=response2, url3=response3, url4=response4, success=True)


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
        elif records and records[0][2] != adminPassword:
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

@app.route("/toSvLogin")
def toSvLogin():
    return render_template('StaffLogin.html') 

@app.route("/toStudPage")
def toStudPage():

    studEmail = request.args.get('studEmail')
   


    fetch_student_sql = "SELECT * FROM student WHERE studEmail = %s"
    cursor = db_conn.cursor()


    try:
        cursor.execute(fetch_student_sql, (studEmail))
        records = cursor.fetchall()

        return render_template('StudPage.html', student=records)

    except Exception as e:
        return str(e)

    finally:
        cursor.close()



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
