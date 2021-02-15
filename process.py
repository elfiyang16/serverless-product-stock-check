from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pandas as pd
import os
from io import StringIO
import io
import boto3
import yaml

from dotenv import load_dotenv
load_dotenv(verbose=True)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']


def gsheets(SPREADSHEET_ID, RANGE_NAME):
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                range=RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        print('{0} rows retrieved.'.format(len(values)))
        
    return values
  
def data_load(values):
    # Insert into DataFrame
    headers = values.pop(0)
    df = pd.DataFrame(values, columns=headers)
    return df
  
def aws_session(region_name='eu-west-1'):
    return boto3.session.Session(aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                                aws_secret_access_key=os.getenv('AWS_ACCESS_KEY_SECRET'),
                                region_name=region_name)
    

def make_bucket(name, acl):
    session = aws_session()
    s3_resource = session.resource('s3')
    return s3_resource.create_bucket(Bucket=name, ACL=acl)
  
  
def upload_to_bucket(df, FILE_NAME):
    # Upload to S3
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index = False, header = True)

    session = aws_session()
    s3 = session.resource('s3')
    s3.Bucket('gsheets-product-data').put_object(Key=FILE_NAME, Body=csv_buffer.getvalue())
    print('csv uploaded to s3://gsheets-data/%s' %(FILE_NAME,))


if __name__ == '__main__':
    # Reads YAML file for all spreadsheets
    file = open("sheets.yml")
    sources =  yaml.load(file, Loader=yaml.FullLoader)
    file.close()

    for x in sources.values():
        values = gsheets(x['spreadsheet_id'], x['range_name'])
        df = data_load(values)
        upload_to_bucket(df, x['filename'])
