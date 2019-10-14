''' 
    lambda to trigger the creation and integration of a sagemaker 
    notebook running on top of an EMR cluster 
'''

import boto3, json, base64, uuid, os

# pulled from CW events 
#event = {'version': '0', 'id': '0371862c-5c4a-01fc-be0c-5cbef0ba7ee6', 'detail-type': 'EMR Cluster State Change', 'source': 'aws.emr', 'account': '592871069658', 'time': '2019-09-15T00:26:06Z', 'region': 'us-east-1', 'resources': [], 'detail': {'severity': 'INFO', 'stateChangeReason': '{"code":""}', 'name': 'My cluster', 'clusterId': 'j-F2AJ8VELYUYX', 'state': 'STARTING', 'message': 'Amazon EMR cluster j-F2AJ8VELYUYX (My cluster) was requested at 2019-09-15 00:26 UTC and is being created.'}}

# pull master IP from the cluster 
def get_master_pvt_ip(client, cluster_id): 
    emr_instance_list = client.list_instances(
        ClusterId=cluster_id, 
        InstanceGroupTypes=['MASTER'],
        InstanceStates=['RUNNING', 'PROVISIONING', 'BOOTSTRAPPING']
    )
    return emr_instance_list['Instances'][0]['PrivateIpAddress']

# configure lifecycle script 
def render_emr_script(master_ip): 
    script = '''
    #!/bin/bash

    set -e 
    nohup pip install --upgrade pip & 

    # this script connects EMR to the Notebook instance 
    # it fails if the master node IP is unreachable 

    # PARAMETERS
    EMR_MASTER_IP={0}

    cd /home/ec2-user/.sparkmagic

    echo "Fetching SparkMagic example config..." 
    wget https://raw.githubusercontent.com/jupyter-incubator/sparkmagic/master/sparkmagic/example_config.json

    echo "Configuring the config... Setting EMR master node IP in SparkMagic config..." 
    sed -i -- "s/localhost/$EMR_MASTER_IP/g" example_config.json
    mv example_config.json config.json

    echo "Sending test request to Livy..." 
    curl "$EMR_MASTER_IP:8998/sessions"   
    '''.format(master_ip)

    b64_encoded = base64.b64encode(script.encode())
    return b64_encoded.decode('ascii') 

# compose CFT 
# in future define in s3 with params, would clean up the code 
def render_cf_template(parameters):
    cf_template_dct = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "CloudFormation template to create simple sagemaker notebook in a subnet",
        "Resources": {
            "sagemakernotebook": {
                "Type": "AWS::SageMaker::NotebookInstance",
                "Properties": {
                    "DirectInternetAccess": "Enabled",
                    "InstanceType": "ml.t2.medium",
                    "LifecycleConfigName": "configName",
                    "NotebookInstanceName": "nbname",
                    "RoleArn": "<>",
                    "RootAccess": "Enabled",
                    "SecurityGroupIds": ["sg-<>"],
                    "SubnetId": "subnet-<>",
                    "VolumeSizeInGB": 5
                }
            }
        }
    }
    
    #user defined parameters:
    cf_template_dct["Resources"]["sagemakernotebook"]["Properties"]["InstanceType"] = parameters["instance_type"]
    cf_template_dct["Resources"]["sagemakernotebook"]["Properties"]["NotebookInstanceName"] = parameters["instance_name"]
    cf_template_dct["Resources"]["sagemakernotebook"]["Properties"]["LifecycleConfigName"] = parameters["lifecycle_config_name"]
    cf_template_dct["Resources"]["sagemakernotebook"]["Properties"]["RoleArn"] = parameters["role_arn"]
    cf_template_dct["Resources"]["sagemakernotebook"]["Properties"]["SecurityGroupIds"] = [parameters["security_group_id"]]
    cf_template_dct["Resources"]["sagemakernotebook"]["Properties"]["SubnetId"] = parameters["subnet_id"]
    cf_template_dct["Resources"]["sagemakernotebook"]["Properties"]["VolumeSizeInGB"] = parameters["volume_size_gb"]

    return json.dumps(cf_template_dct)

''' UPDATE: September 18  
Adding dynamoDB writes 
'''
# def update_dynamo(client, _id): 
#   return client.put_item(
#     TableName='ds-pipeline-notebooks',
#     Item={
#         'NotebookId': {
#             'S': _id
#         }
#     }
#   ) ON HOLD FOR NOW 

# AWS clients (in future, don't hard code region. Pass as param)
REGION = os.environ['AWS_REGION']
cft = boto3.client('cloudformation', region_name=REGION)
sagemaker = boto3.client('sagemaker', region_name=REGION)
emr = boto3.client('emr', region_name=REGION)
ssm = boto3.client('ssm', region_name=REGION)
dynamo = boto3.client('dynamodb', region_name=REGION)

def handler(event, context):
    # print('Generating UUID...')
    # nb_id = uuid.uuid4()
    # update_dynamo(dynamo, str(nb_id))
    # print('[[INFO]] Notebook {} saved to dynamo'.format(nb_id))

    parameters = {
        'security_group_ids': [],
        'subnet_id': None,
        'cluster_id': None,
        'volume_size_gb': 5, 
        'role_arn': None,
        'instance_type': 'ml.t2.medium',
        'instance_name': 'sagemaker-core',
        'lifecycle_config_name': 'SparkBoot',
        'stack_name': None
    }

    print('Cluster ID:', event['detail']['clusterId'])
    print('Verifying tags...')
    # verify that the named cluster is routed for sparkmaker 
    cluster_info = emr.describe_cluster(
      ClusterId=event['detail']['clusterId']
    )
    
    try: 
      tags = cluster_info['Cluster']['Tags'][0]
      values = tags.values()
      print('[[TAGS]]', values)
      if 'Sparkmaker' not in values: 
        return 
    except: 
      print('Could not identify sparkmaker tags. Aborting.')
      return 
    print('Tags found. Carrying on...')


    # pull parameters from ssm and event 
    parameters['cluster_id'] = event['detail']['clusterId']
    parameters['stack_name'] = event['detail']['name'].replace(' ', '') + '-SageMakerLink'
    parameters['lifecycle_config_name'] = parameters['lifecycle_config_name'] + parameters['cluster_id']
    setup_params = ssm.get_parameters_by_path(
        Recursive=True,
        Path='/setup',
        MaxResults=10
    )
    role_params = ssm.get_parameters_by_path(
        Recursive=True,
        Path='/setup/roles',
        MaxResults=10
    )
    print(setup_params)
    
    for entry in setup_params['Parameters']: 
        if (entry['Name'].find('PublicSubnetId') >= 0): 
            parameters['subnet_id'] = entry['Value']
        
        elif (entry['Name'].find('NotebookSecurityGroup') >= 0): 
            parameters['security_group_id'] = entry['Value']
    
    for entry in role_params['Parameters']: 
        if (entry['Name'].find('NotebookRole') >= 0): 
            parameters['role_arn'] = entry['Value']
    
    print(parameters['role_arn'])
    parameters['instance_name'] = parameters['instance_name'] + '-' + parameters['cluster_id']
    
    # obtain private ip of master node 
    master_private_ip = get_master_pvt_ip(emr, parameters['cluster_id'])
    
    # create lifecycle configuration 
    print('Checking to see if lifecycle config exists...')
    try: 
        config = sagemaker.describe_notebook_instance_lifecycle_config(
                NotebookInstanceLifecycleConfigName=parameters['lifecycle_config_name']
                )
    except: 
        print('Creating lifecycle configuration...')
        config = sagemaker.create_notebook_instance_lifecycle_config(
            NotebookInstanceLifecycleConfigName=parameters['lifecycle_config_name'],
            OnCreate=[{ 'Content': render_emr_script(master_private_ip) }],
            )
    
    sagemaker_cft = render_cf_template(parameters)
    print('Provisioning SageMaker notebook...')
    stack_response = cft.create_stack(
        StackName=parameters["stack_name"],
        TemplateBody=sagemaker_cft,
        ResourceTypes=['AWS::SageMaker::NotebookInstance'],
        OnFailure='ROLLBACK', 
        EnableTerminationProtection=False
        )
    
    # print('Generating UUID...')
    # nb_id = uuid.uuid4()
    # update_dynamo(dynamo, str(nb_id))
    # print('Write complete...')
    


