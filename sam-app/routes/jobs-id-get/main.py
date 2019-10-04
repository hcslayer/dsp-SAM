''' /jobs/{id} [GET] 
  Retrieves information about a specific job
'''

import boto3, json, os
dynamo = boto3.resource("dynamodb", region_name=os.environ["AWS_REGION"])

def handler(event, context):
    #jobId = event["id"]
    print('[[EVENT]]', event) 
    table = dynamo.Table("Jobs") 
    try:
        db_response = table.get_item(
          Key={
            'JobId': '9fccf84b-7aad-4b0d-8561-915f49107e79'
          }
        )

    except Exception as err: 
        print("[[ERROR]]", err)
        print("[[ERROR]] An error occurred while searching for the job.")
        print("The specified job may not exist, or may have been deleted.")

    return {"headers": { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}, "body": json.dumps({"data": db_response})}

