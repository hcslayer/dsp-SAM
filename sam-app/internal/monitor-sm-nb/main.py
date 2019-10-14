''' FROM < tm-monitor-nb > 
    lambda function to monitor a sagemaker notebook.  
    Reads from cloudwatch events to pull the notebook status.  
'''
import json, boto3, os
#dynamo = boto3.client('dynamodb', region_name='us-east-1')
# AWS clients (in future, don't hard code region. Pass as param)
REGION = os.environ['AWS_REGION']
dynamo = boto3.resource('dynamodb', region_name=REGION)
sagemaker = boto3.client('sagemaker', region_name=REGION)

def handler(event, context):
  print('[[EVENT]]', event)

  table = dynamo.Table('Notebooks')
  try:
    ## event is literally the cloudwatch event
    uuid_from_tags = event["detail"]["Tags"]["UUID"]
    nb_status = event["detail"]["NotebookInstanceStatus"]
    nb_name = event["detail"]["NotebookInstanceName"]

    nb_status = event["detail"]["NotebookInstanceStatus"]

    ## using sagemaker sdk instead of cloudwatch because its more accurate
    ## for some reason Cloudwatch was returning Pending when noteobok is InService
    sagemaker_response = sagemaker.describe_notebook_instance(
      NotebookInstanceName=nb_name
    )

    sm_state = sagemaker_response["NotebookInstanceStatus"]
    print("[][][][] SM STATE {} [][][]][]".format(sm_state))

    update_response = table.update_item(
      Key={'NotebookId': uuid_from_tags}, 
      UpdateExpression="SET Nb_status = :s", 
      ExpressionAttributeValues={':s': sm_state}, 
      ReturnValues="UPDATED_NEW")

    print("UPDATE RESPONSE: ", update_response)
    print("Item updated in DYNAMO")
  except Exception as e:
    print("[[ INFO ]] Sagemaker has not yet returned all the data {}".format(e))

  return {
    'statusCode': 200,
    'body': json.dumps('Hello from Lambda!')
  }
