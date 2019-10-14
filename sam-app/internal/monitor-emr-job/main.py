''' FROM < tm-monitor-job > 
    A logging lambda to populate the front end with EMR cluster events. 
    A cloudwatch event will be configured to listen to EMR for any events 
    The appropriate state changes will be parsed by the lambda, and piped 
    to dynamo, if they're of value. 
'''

''' EVENT CONFIG -> for internal / cft use 
{
  "source": [
    "aws.emr"
  ],
  "detail-type": [
    "EMR Step Status Change",
    "EMR Cluster State Change",
  ]
}

the 'detail' subfield of the event is what we want 
'''

import boto3, os, json

REGION = os.environ['AWS_REGION']
dynamo = boto3.resource('dynamodb', region_name=REGION)
emr = boto3.client('emr', region_name=REGION)

def handler(event, context):
  print('[[EVENT]]', event)
  table = dynamo.Table("Jobs")
  
  try: 
    # entry = event['detail'] # this will give us a full blob with all sorts of interesting details. 
    clusterId = event["detail"]["clusterId"]
    describe_response = emr.describe_cluster(
      ClusterId=clusterId
    )
    
    #print("DESCRIBE RES")
    UUID = describe_response["Cluster"]["Tags"][0]["Value"]
    
    last_log = event["detail"]
    
    print('[[[CLUSTER ID ===> ]]]')
    print(clusterId)
    print('[[[LAST LOGGGG ===> ]]]')
    print(last_log)
    
    update_response = table.update_item(
      Key={'JobId': UUID},
      UpdateExpression="SET LastLog = :s",
      ExpressionAttributeValues={':s': last_log},
      ReturnValues="UPDATED_NEW")
  except Exception as e: 
    print('[[ERROR]] An error occured while parsing the event.')
    print(e)