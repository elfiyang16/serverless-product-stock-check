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
import botocore
import yaml
from datetime import datetime


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
  
def aws_session():
    return boto3.session.Session(aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                                aws_secret_access_key=os.getenv('AWS_ACCESS_KEY_SECRET'),
                                region_name=os.getenv('REGION'))
    

def make_bucket(name, acl):
    session = aws_session()
    s3_resource = session.resource('s3')
    return s3_resource.create_bucket(Bucket=name, ACL=acl)
  
  
def upload_to_bucket(df, FILE_NAME, BUCKET_NAME='gsheets-product-data'):
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index = False, header = True)

    session = aws_session()
    s3 = session.resource('s3')
    s3.Bucket(BUCKET_NAME).put_object(Key=FILE_NAME, Body=csv_buffer.getvalue())
    print(f"csv uploaded to s3://{BUCKET_NAME}/{FILE_NAME}")

def download_from_bucket(FILE_NAME, BUCKET_NAME='gsheets-product-data'):
    session = aws_session()
    s3 = session.client('s3')
    
    try:
      obj = s3.get_object(Bucket=BUCKET_NAME, Key=FILE_NAME)
    except botocore.exceptions.ClientError as e:
      if e.response['Error']['Code'] == "404":
        print("The file does not exist.")
      else:
        raise
    df = pd.read_csv(io.BytesIO(obj['Body'].read()), encoding='utf8')
    df.to_json (path_or_buf=f'./downloaded/{str(datetime.now())}.json')
    print(f'download csv object {FILE_NAME} from {BUCKET_NAME}')
  

if __name__ == '__main__':
    file = open("sheets.yml")
    sources =  yaml.load(file, Loader=yaml.FullLoader)
    file.close()

    for x in sources.values():
        values = gsheets(x['spreadsheet_id'], x['range_name'])
        df = data_load(values)
        upload_to_bucket(df, x['filename'])
        download_from_bucket(x['filename'])
