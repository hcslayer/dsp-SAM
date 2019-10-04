''' setup.py 
    A python script to configure the foundations of the DSP-SAM 
    environment. 
'''
import pyfiglet, boto3, sys, os, subprocess, shlex, time

# utilities 

# CLI progress bar 
def printProgressBar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end = '\r')
    # Print New Line on Complete
    if iteration == total: 
        print()

# ascii banner 
banner = pyfiglet.figlet_format('DSP-SAM')

def main(): 
  print(banner) 
  print(
  '''
  Welcome to the productOps Data Science Platform! 
  Before continuing, please be sure that the 'template-resources/'
  and 'emr-resources/' directories are populated with the templates 
  and scripts that you would like to initialize on environment 
  creation. Additionally, please ensure that your AWS CLI credentials 
  have been properly configured for the target account.
  ''') 
  spacer = input('Continue? [y/n]')
  if (spacer == 'n'): 
    return 
  
  print(
  '''
  Define a name for your environment. Due to AWS resource name 
  length limits, try to keep this prefix relatively short. 
  The environment name you choose will become a global bucket 
  and stack prefix. 
  ''')
  prefix = input()
  
  print('''
  Enter the AWS Region you would like to deploy the evironment 
  in. (ex: us-east-1, eu-west-2, etc)
  ''')
  region = input() 

  print('...initializing boto3 clients')
  s3 = boto3.client('s3', region_name=region)
  ssm = boto3.client('ssm', region_name=region)
  cft = boto3.client('cloudformation', region_name=region)


  print('Complete! Provisioning storage....')
  # create s3 bucket 
  try: 
    bucket_response = s3.create_bucket(
      ACL='private',
      Bucket='{}-core-src'.format(prefix),
      CreateBucketConfiguration={
        'LocationConstraint': region
      },
      # FOR LATER ? 
      # GrantFullControl='string',
      # GrantRead='string',
      # GrantReadACP='string',
      # GrantWrite='string',
      # GrantWriteACP='string',
      # ObjectLockEnabledForBucket=True|False
    )
    bucket_response2 = s3.create_bucket(
      ACL='private',
      Bucket='{}-emr-resources'.format(prefix),
      CreateBucketConfiguration={
        'LocationConstraint': region
      },
      # FOR LATER ? 
      # GrantFullControl='string',
      # GrantRead='string',
      # GrantReadACP='string',
      # GrantWrite='string',
      # GrantWriteACP='string',
      # ObjectLockEnabledForBucket=True|False
    )
  except Exception as e: 
    print('[[ERROR]]: S3 Failure on bucket creation.')
    print(e)
    return 


  # upload the target resources
  cft_bucket = 's3://{}-core-src'.format(prefix)
  emr_bucket = 's3://{}-emr-resources'.format(prefix)
  try: 
    upload_output = subprocess.call(shlex.split('./upload_resources.sh {} {}'.format(cft_bucket, emr_bucket)))
  except Exception as e: 
    print('[[ERROR]]', e)
    return 
  
  # on success, write parameters to SSM and run the networking template 
  try: 
    ssm.put_parameter(
      Name='/setup/BucketPrefix',
      Description='Global bucket and stack identifier prefix.',
      Value=prefix,
      Type='String',
      Overwrite=True
    )
  except Exception as e: 
    print('[[ERROR]]', e)
    return
  
  # build network stack 
  print('BUILDING NETWORK STACK ==> ')
  print('This may take several moments.....')
  bucket_url = 'http://s3-{}.amazonaws.com/{}-core-src'.format(region, prefix)
  #emr_bucket = 'http://s3-{}.amazonaws.com/{}-emr-resources'.format(region, prefix)
  try: 
    cft.create_stack(
      StackName='{}-network'.format(prefix),
      TemplateURL='{}/setup-network.yaml'.format(bucket_url),
      Parameters=[
        {
        'ParameterKey': 'VPCName',
        'ParameterValue': '{}-VPC'.format(prefix)
        }
      ],
      OnFailure='DELETE',
      EnableTerminationProtection=False
    )
    # this would be the place to include some type of graphic 
    # or an updating status
    STACK_STATUS = 'CREATE_IN_PROGRESS'
    print('STATUS: ')
    time_elapsed = 0 
    while (STACK_STATUS != 'CREATE_COMPLETE'):
      res = cft.describe_stacks(
        StackName='{}-network'.format(prefix)
      )
      STACK_STATUS = res['Stacks'][0]['StackStatus']
      events = cft.describe_stack_events(
        StackName='{}-network'.format(prefix)
      )['StackEvents']

      for event in events: 
        print('[[LATEST]] ', event['LogicalResourceId'], ' ==> ', event['ResourceStatus'], end='\r')
        time.sleep(1)
      
      print('> > > ', STACK_STATUS, ' time elapsed {}s'.format(time_elapsed), end='\r')
      time.sleep(5)
 
         
  except Exception as e: 
    print('[[ERROR]]', e)
    return 
  print() 
  print('SETUP COMPLETE')
  



if __name__ == '__main__': 
  main() 
