''' /jobs [GET] 
    This function is responsible for querying dynamo for the status 
    of recently-created EMR jobs. This data is then used to populate 
    the front end. 
'''

import boto3, os, json, uuid, datetime

dynamo = boto3.client('dynamodb', region_name=os.environ['AWS_REGION'])

def handler(event, context):
    db_response = dynamo.scan(
        TableName="Jobs"
        )
    items = db_response["Items"]
    print(items)
    
    return {"data": {"items": items}  }