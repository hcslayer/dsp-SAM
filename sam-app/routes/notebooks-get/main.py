''' /notebooks/GET
    This lambda function scans Dynamo, and returns updated notebook status
    information. 
'''

import boto3, os, json, uuid, datetime

dynamo = boto3.client('dynamodb', region_name=os.environ['AWS_REGION'])

def handler(event, context):
    db_response = dynamo.scan(
        TableName="Notebooks"
        )
    items = db_response["Items"]
    print(items)
    
    return {"data": {"items": items}  }