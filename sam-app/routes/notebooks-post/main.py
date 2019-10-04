''' standalone-nb
  Lambda responsible for provisioning a standard sagemaker notebook

  Parameters: 
    The template that lives in S3 is highly configurable, but the only real 
    parameter needed for a quick deployment is the name of the notebook. 
    REQUIRED: 
      Name 
    OPTIONAL: 
      MainRepository, Public(y/n), HasRootAccess, NotebookInstanceType, 
      VolumeSize, Accelerator, CustomLifecycleConfig, Subnet, SecurityGroup
      StreetSweeperTarget
  
  Ideally, we pass USE_DEFAULTS as an additional parameter, to indicate what's coming
  down the pipe 
'''

import boto3, os, json, uuid, datetime

dynamo = boto3.client('dynamodb', region_name=os.environ['AWS_REGION'])
cft = boto3.client('cloudformation', region_name=os.environ['AWS_REGION'])
ssm = boto3.client('ssm', region_name=os.environ['AWS_REGION']) 

def handler(event, context):
  try: 
    bucket_prefix = ssm.get_parameter(Name='/setup/BucketPrefix')['Parameter']['Value']
  except Exception as err:
    print('[[ERR]]: An ssm error has occurred ERROR: {}'.format(err))
    return
    
  template_path = 'https://' + bucket_prefix + '-core-src.s3.amazonaws.com/sagemaker.yaml'
  
  # cloudformation template parameters :: see sagemaker.yaml 
  params = {
    'Name': '',
    'MainRepository': '',
    'Public': 'yes', 
    'HasRootAccess': 'Enabled', 
    'NotebookInstanceType': 'ml.t2.medium', 
    'VolumeSize': '5',
    'Accelerator': 'None', 
    'CustomLifecycleConfig': 'None', 
    'Subnet': 'Setup Default - Public', 
    'SecurityGroup': '', 
    'StreetSweeperTarget': 'no', 
    'UUID': ''
  } 
  notebookId = str(uuid.uuid4())
  createdAt = str(datetime.datetime.now())
  params['UUID'] = notebookId

  print("EVENT: =>", event)
  # set parameters to reflect event values 
  if 'Name' not in event.keys(): 
    print('Request err: notebook name not specified')
    return 
  for key in event.keys(): 
    params[key] = event[key]
  
  # write values to dynamo 
  dynamo.put_item(TableName='Notebooks', 
    Item={'NotebookId':{'S': params['UUID']}, 
    'Name': {'S': params["Name"]}, 
    'InstanceType': {'S': params["NotebookInstanceType"]}, 
    'VolumeSize': {'S': params["VolumeSize"]}, 
    'Timestamp': {'S': createdAt},
    'Nb_status': {'S': 'Initiated'}
    })
  print("Item written to DYNAMO: {} {}".format(params["Name"], params["UUID"]))
  
  # set values in a cloudformation-friendly format 
  param_dict = []
  for key in params.keys(): 
    param_dict.append(
      {
      'ParameterKey': key, 
      'ParameterValue': params[key]
      }
    )
  
  print("PARAM DICT: => ", param_dict)
  
  cft_response = cft.create_stack(
    StackName='nb-' + params['Name'] + notebookId,
    TemplateURL=template_path,
    Parameters=param_dict,
    OnFailure='DELETE' 
  )
  
  return json.dumps({"statusCode":200, "headers":{"Access-Control-Allow-Origin": "*" }, "body": {"cft_response": cft_response, "notebookId": notebookId, "notebookName": event["Name"] }})