''' PLACEHOLDER: JOBS/ routes are under construction
'''

import boto3, os, json

def handler(event, context): 
  print('[[EVENT]]', event)
  res = {
    "statusCode": 200,
    "headers": {"Access-Control-Allow-Origin": "*"},
    "body": "request recieved"
  }
  return res 