''' /jobs [POST]
  This lambda is responsible for creating a cloudwatch rule.
  The rule that is created is responsible for launching an EMR job when 
  cron expression conditions are met.
  This function assumes the existence of a global BUCKET_PREFIX parameter, 
  and the presence of an S3 bucket populated with infrastructure templates. 
'''
import boto3
import json
import os
import datetime
REGION = os.environ["AWS_REGION"]

cft = boto3.client("cloudformation", region_name=REGION)
dynamo = boto3.client("dynamodb", region_name=REGION)
ssm = boto3.client("ssm", region_name=REGION)
lambo = boto3.client("lambda", region_name=REGION)

BUCKET_PREFIX = ssm.get_parameter(
    Name="/setup/BucketPrefix")["Parameter"]["Value"]

template_path = "https://{}-core-src.s3.amazonaws.com/create-scheduled-job-event-rule.yaml" \
                .format(BUCKET_PREFIX)

def handler(event, context):
    run_on_init = event["run_on_init"]
    rule_name = event["rule_name"]
    job_id = event["job_id"]
    job_name = event["job_name"]
    schedule = event["schedule"]
    if event["schedule"]:
        minute_interval = event["schedule"][0]
        parameter_map = [
            {'ParameterKey': 'EventName', 'ParameterValue': rule_name},
            {'ParameterKey': 'Minute', 'ParameterValue': minute_interval},
            {'ParameterKey': 'Hour', 'ParameterValue': '*'},
            {'ParameterKey': 'Day', 'ParameterValue': '*'},
            {'ParameterKey': 'Month', 'ParameterValue': '*'},
            {'ParameterKey': 'DayOfWeek', 'ParameterValue': '?'},
            {'ParameterKey': 'Year', 'ParameterValue': '*'},
            {'ParameterKey': 'Payload',
             'ParameterValue': json.dumps(event)}
        ]

    created_at = str(datetime.datetime.now())

    if schedule:
        print(" == Running EMR-Runner\n Creating Event in Cloudwatch")
        try:
            print("[[INFO]] STARTING RULE STACK BUILD")
            stack_response = cft.create_stack(
                StackName=rule_name,
                TemplateURL=template_path,
                Parameters=parameter_map,
                OnFailure='DELETE')
            print("[[INFO]] CREATING CW RULE")

            dynamo.put_item(TableName='Jobs',
                            Item={'JobId': {'S': job_id},
                                  'JobName': {'S': job_name},
                                  'Schedule': {'S': str(schedule) if schedule else 'NotRecurring'},
                                  'RunOnInit': {'S': str(run_on_init)},
                                  'TriggeredBy': {'S': rule_name if schedule else 'OneOff'},
                                  'LastLog': {'S': 'No logs yet'}, 
                                  'Timestamp': {'S': created_at}, })

            print(" == Added to Dynamo")
        except Exception as e:
            print('[[ERROR]] Encountered an error building the event rule. Please check logs. ==>')
            print(e)

    elif run_on_init and (schedule is None):
        ## RUN JOB NOW BUT DON"T SCHEUDLE, trigger emr-job-runner here
        print(" == Running the job now\n No Cloudwatch")
        try:
            lambo.invoke(
                FunctionName='tm-emr-job-runner',
                InvocationType='Event',
                LogType='Tail',
                # gets passed to emr-job-runner function
                Payload=json.dumps(event)
            )
            dynamo.put_item(TableName='Jobs',
                            Item={'JobId': {'S': job_id},
                                  'JobName': {'S': job_name},
                                  'Schedule': {'S': str(schedule) if schedule else 'NotRecurring'},
                                  'RunOnInit': {'S': str(run_on_init)},
                                  'TriggeredBy': {'S': rule_name if schedule else 'OneOff'},
                                  'Timestamp': {'S': created_at}, })

            print(" == Added to Dynamo")
        except Exception as e:
            print(
                '[[ERROR]] Encountered an error running the emr-job-runner. Please check logs.')
            print(e)
    print(event)

    return json.dumps({"statusCode": 200, "headers": {"Accesss-Control-Allow-Origin": "*"}, "body": {"create-job-lambda": "COMPLETED SUCCESSFULLY"}})
