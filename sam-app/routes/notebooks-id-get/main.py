''' Lambda function to test the subresource capabilities of the SAM model. 

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
      "body": json.dumps(event)
    }

    return res