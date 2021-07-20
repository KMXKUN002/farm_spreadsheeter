import os
import psycopg2
from email_validator import validate_email, EmailNotValidError
import requests
from datetime import datetime
from smtplib import SMTPException
from get_column_names_from_table import get_col_names
from xl_maker import create_workbook
from emailer import send_mail

# Name for excel file
filename = "Farm Data.xlsx"

# Edit this list if adding more device types to database
device_type_list = [
    "valves",
    "pumps",
    "soil",
    "ec"
]

# Messages indicating the outcome of farm_spreadsheeter()
return_message = {
    'invalid_date': "Invalid dates. Start date must come before end date.\n",
    'invalid_email': "Invalid email.\n",
    'nonexistent_email': "This email does not exist.\n",
    'connection_error': "Error connecting to email checking API.\n",
    'database_error': "There has been an error while connecting to or querying the database.\n",
    'email_sending_error': "Error sending email. See details:\n",
    'successful': "Excel file successfully sent to mail.\n"
}


def does_email_exist(email):
    try:
        response = requests.get(
            "https://isitarealemail.com/api/email/validate",
            params={'email': email})
        status = response.json()['status']
        return status == "valid"
    except ConnectionError as c:
        return str(c)


def are_dates_ordered(start_date, end_date):
    date_format = "%Y-%m-%d"
    start_date_obj = datetime.strptime(start_date, date_format)
    end_date_obj = datetime.strptime(end_date, date_format)
    return start_date_obj <= end_date_obj


def get_table_query(farm_id, device_type, col_names, start_date, end_date):
    """
    :param farm_id:
    :param device_type: one of [valves, pumps, soil, ec]
    :param col_names: list of column names of the table
    :param start_date: formatted 'YYYY-MM-DD'
    :param end_date:
    :return: string query
    """

    # Format column names into a single string, putting each name in between quotation marks
    col_names_string = ",".join(f"\"{c}\"" for c in col_names)

    # Format query
    query = f"select {col_names_string}" \
            f"from {device_type}_{farm_id} " \
            f"where timestamp >= '{start_date}' and timestamp <= '{end_date}' " \
            f"order by timestamp DESC"
    return query


# Fetch data from cursor
def fetch_data(cur, query):
    cur.execute(query)
    data = cur.fetchall()
    return data


def farm_spreadsheeter(farm_id, incoming_data, conn):
    """
    :param farm_id: numerical ID string, eg. 2147483551
    :param incoming_data:   {
                                "email": The email to send the data to
                                "start_date": Only data from this date on is sent
                                "end_date": Only data before this date is sent
                            }
    :param conn: A psycopg2 connection object
    :return: (error_code, return_message)
            error_code is -1 if error exists, 0 if no error
    """
    # Validate dates
    start_date = incoming_data['start_date']
    end_date = incoming_data['end_date']
    if not are_dates_ordered(start_date, end_date):
        return -1, return_message['invalid_date']

    # Validate email
    try:
        valid = validate_email(incoming_data["email"])
        email = valid.email
    except EmailNotValidError as e:
        return -1, return_message['invalid_email'] + str(e)

    # Check if email exists
    email_exists = does_email_exist(email)
    if isinstance(email_exists, str):
        return -1, return_message['connection_error'] + email_exists
    elif not email_exists:
        return -1, return_message['nonexistent_email']

    # Retrieve data from server
    device_data = {}  # Dictionary of data for each device type
    col_names = {}  # Dictionary of column names for each device type
    try:
        with conn.cursor() as cur:
            for device_type in device_type_list:
                # print("Columns for "+device_type)
                col_names[device_type] = get_col_names(cur, f"{device_type}_{farm_id}")
                query = get_table_query(farm_id,
                                        device_type,
                                        col_names[device_type],
                                        start_date, end_date)
                device_data[device_type] = fetch_data(cur, query)
    except psycopg2.Error as e:
        return -1, return_message['database_error'] + str(e)
    print(device_data)

    # Generate excel file
    create_workbook(col_names, device_data, filename)

    # Email excel file
    subject = f"Farm data from {start_date} to {end_date}"
    try:
        send_mail(email, subject, filename)
    except SMTPException as e:
        return -1, return_message['email_sending_error'] + str(e)

    # Delete excel file from disk
    if os.path.exists(filename):
        os.remove(filename)

    # If everything is successful, return success message
    return 0, return_message['successful']


if __name__ == "__main__":
    # Input parameter for function
    farm_id = "2147483551"

    # Input parameter for function Example
    incoming_data = {
        "email": "lodiconfarmtest@gmail.com",
        "start_date": "2021-07-10",
        "end_date": "2021-07-14",
    }

    # Psycopg2 connection object
    conn = psycopg2.connect(database="d6e51l63343226", user="qlaqtrzvxkkslz",
                            password="0f1411c3f0e45ed5a610937c9da7eaa43ecbfc00ed65ba76b0a000a656ca9a47",
                            host="ec2-52-31-233-101.eu-west-1.compute.amazonaws.com", port="5432")
    print(farm_spreadsheeter(farm_id, incoming_data, conn)[1])
