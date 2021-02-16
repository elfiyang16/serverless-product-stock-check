import os
import boto3
from botocore.exceptions import ClientError
import csv
from io import StringIO, BytesIO
import pandas as pd


BUCKET_NAME='gsheets-product-data'
KEY = 'product_list.csv'

# def aws_session():
#     return boto3.session.Session(aws_access_key_id=os.getenv('ACCESS_KEY_ID'),
#                                 aws_secret_access_key=os.getenv('ACCESS_KEY_SECRET'),
#                                 region_name='eu-west-1')
def stock_check(event,context):
    # auth
    # session = aws_session()
    # s3 = session.client('s3')
    s3 = boto3.client('s3')
    
    # download the file
    try:
      obj = s3.get_object(Bucket=BUCKET_NAME, Key=KEY)
    except ClientError as e:
      if e.response['Error']['Code'] == "404":
        print("The file does not exist.")
      else:
        raise
    
    # look for stock fail under 0
    df = pd.read_csv(BytesIO(obj['Body'].read()), encoding='utf8', converters={'Quantity': int})
    prodObj = pd.DataFrame(df,  columns=['Name','Quantity', "Vendor_Email"])
    noStockObj = pd.DataFrame(columns=['Name','Vendor_Email'])

    for index, row in prodObj.iterrows():
        if row['Quantity'] == 0 :
            noStockObj = noStockObj.append({'Name': row['Name'], 'Vendor_Email':row['Vendor_Email']}, ignore_index=True)
   
    # upload logger to s3 no_stock_alert.json
    if not noStockObj.empty:
        jsonBuffer = StringIO()
        noStockObj.to_json(jsonBuffer)
        try:
            s3.put_object( Bucket=BUCKET_NAME, Key='no_stock_alert.json',Body=jsonBuffer.getvalue())
        except ClientError as e:
            raise e

    return {
        'message': 'susccessfully completes stock check'
    }
    
    

# if __name__ == '__main__':
#     stock_check()