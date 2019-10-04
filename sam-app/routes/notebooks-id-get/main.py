''' /notebooks/{id}/GET
    Lambda function to return the web-accessible URL of a SageMaker Notebook 
    or an EMR-backed notebook. 
    The URL is only valid for 5 minutes before it expires. 
'''

import boto3, json, os

sagemaker = boto3.client("sagemaker", region_name=os.environ["AWS_REGION"])
dynamo = boto3.resource("dynamodb", region_name=os.environ["AWS_REGION"])

def get_url(client, nb_name): 
    response = client.create_presigned_notebook_instance_url(
        NotebookInstanceName=nb_name
    )
    return response['AuthorizedUrl']

def lambda_handler(event, context): 
  notebookId = event["pathParameters"]["id"]
  table = dynamo.Table("Notebooks") 

  try:
    db_response = table.get_item(
      Key={
        'NotebookId': notebookId
      }
    )

    nb_name = db_response["Item"]["Name"]
    # verify that notebook exists 
    # return URL 
    url = get_url(sagemaker, nb_name)
    print("URL: ", url)
  except Exception as err: 
    print("[[ERROR]]", err)
    print("[[ERROR]] An error occurred while searching for notebook.")
    print("The specified notebook may not exist, or may be turned off.")
    return 
  

  return {"headers": { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}, "body": json.dumps({"notebookUrl": url})}
