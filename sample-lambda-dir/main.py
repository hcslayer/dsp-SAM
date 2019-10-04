''' Add a useful comment block here about the role of the function, any 
	 dependencies or preconditions, as well as the other lambdas that it 
	 may be tangled with. 
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
