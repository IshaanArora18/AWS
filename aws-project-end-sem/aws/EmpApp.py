
from flask import Flask, render_template, request, redirect, url_for,flash
import secrets
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

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
table = 'employee'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('AddEmp.html')


@app.route("/about", methods=['GET'])
def about():
    return redirect('https://thisismystudentbucket1.s3.amazonaws.com/static.html')

@app.route("/update", methods=['GET'])
def update():
    return render_template('update_Emp.html')


@app.route("/getemployee", methods=['GET'])
def getstudent():
    return render_template('GetEmp.html')

@app.route("/deleteemployee", methods=['GET'])
def deletestudent():
    return render_template('delete.html')


##########################################################################################################################################
#adding info of student ........

@app.route("/addemp", methods=['POST'])
def AddStu():
    emp_id = request.form['emp_id']
    name = request.form['name']
    dob = request.form['dob']
    phonenumber = request.form['phonenumber']
    address = request.form['address']
    stu_image_file = request.files['stu_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if stu_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, name, dob, phonenumber, address))
        db_conn.commit()
        stu_name = "" + name + " " + dob
        # Uplaod image file in S3 #
        stu_image_file_name_in_s3 = "stu-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=stu_image_file_name_in_s3, Body=stu_image_file)
            bucket_address = boto3.client('s3').get_bucket_address(Bucket=custombucket)
            s3_address = (bucket_address['addressConstraint'])

            if s3_address is None:
                s3_address = ''
            else:
                s3_address = '-' + s3_address

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_address,
                custombucket,
                stu_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=stu_name)

#############################################################################################################################################3


# updating the student if it present in the data base ....

# updating the student if it present in the data base ....

@app.route("/updateEmp", methods=['POST'])
def updateEmp():
    # Retrieve the student information from the form
    emp_id = request.form['emp_id']
    name = request.form['name']
    dob = request.form['dob']
    phonenumber = request.form['phonenumber']
    address = request.form['address']

    cursor = db_conn.cursor()

    try:
        # Check if student with given ID already exists
        cursor.execute("SELECT * FROM employee WHERE emp_id = %s", (emp_id,))
        existing_student = cursor.fetchone()

        if existing_student:
            # Student with the same ID exists, update the record
            update_sql = "UPDATE employee SET name = %s, dob = %s, phonenumber = %s, address = %s WHERE emp_id = %s"
            cursor.execute(update_sql, (name, dob, phonenumber, address, emp_id))
            db_conn.commit()

            stu_name = f"{name} {dob}"
            return render_template('AddEmpOutput.html', name=stu_name)
        else:
            # flash("Invalid: Student ID not found.", 'error')
            return render_template('AddEmpOutput.html', name=stu_name)

    finally:
        cursor.close()




#######################################################################################################################
        
#getting the data from the database.
@app.route("/display_data", methods=['POST'])
def display_data():
    emp_id = request.form.get('emp_id', type=int)
    if emp_id is not None:
        cursor = db_conn.cursor()
        try:
            # Fetch data for the specific student ID
            cursor.execute("SELECT * FROM employee WHERE emp_id = %s", (emp_id,))
            student_data = cursor.fetchone()
            print(emp_id , student_data)
            if student_data:
                # Render the HTML template with the student data
                print("fetch successfully")
                return render_template('GetEmpOutput.html', data=student_data)
            else:
                error_message = f"Student with ID {emp_id} not found."
                # flash('Error: Something went wrong!', 'error')
                return redirect(url_for('getstudent', error_message=error_message))

        finally:
            cursor.close()
    else:
        error_message = f"Please Enter a Valid Employee Id."
        # flash("Enter a Valid Id", 'error')
        return redirect(url_for('getstudent', error_message=error_message))
    
##############################################################################################################################################
#delete entry
@app.route("/delete", methods=['POST'])
def DeleteEmp():
    # Retrieve the student ID from the form
    emp_id = request.form['emp_id']

    cursor = db_conn.cursor()

    try:
        # Check if student with given ID exists
        cursor.execute("SELECT * FROM employee WHERE emp_id = %s", (emp_id,))
        existing_student = cursor.fetchone()

        if existing_student:
            # Student with the given ID exists, delete the record
            delete_sql = "DELETE FROM employee WHERE emp_id = %s"
            cursor.execute(delete_sql, (emp_id,))
            db_conn.commit()

            return render_template('AddEmpOutput.html', name=emp_id)
        else:
            # flash("student id is not found", 'error')
            return render_template('delete.html', name=emp_id)

    finally:
        cursor.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
