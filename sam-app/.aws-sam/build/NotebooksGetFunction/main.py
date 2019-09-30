''' NotebooksGetFunction 
    This is a test function for the SAM application model. 
    It prints the event to stdout, and then returns a 200 status code. 
'''

import boto3, json, os

REGION = os.environ['AWS_REGION']
ENV = os.environ['APP_ENV']

def handler(event, context): 
    print('[[EVENT]]', event)
    print('[[ENV]]', ENV)

    res = {
      "statusCode": 200,
      "headers": {
        "Access-Control-Allow-Origin": "*"
      },
      "body": "request recieved"
    }

    return res 