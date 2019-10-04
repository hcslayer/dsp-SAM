# Data Science Platform -- SAM Redux 

The Serverless Application Model smooths out some of the difficulties that we were facing while abstracting AWS services to the front end. In particular, it supports seamless Lambda/ApiG integration, and takes care of all those invisible IAM roles that keep services chirping and happy. 

So, this repo recognizes an attempt to convert the "pure" CloudFormation architecture over to the semi-managed SAM model. 

## Workflow 

*Note: this workflow assumes that you have a designated S3 bucket to do all of the SAM-app things.* 

While developing in the SAM environment, there's some neat tricks that support a continuous dev process without needing to enter the console. 
In broad strokes, the workflow consists of **Build, Package, Deploy**. 

**Build** compiles the dependencies for the Lambda functions. In our use case, we've opted for a Python3.7/Boto3 configuration, and that's the way that it's going to stay for the foreseeable future. Build is essential, as it produces the artifacts required for the Package and Deploy stages. On a high level, it *compiles* the SAM app. 

After Build, you can Package your application for Console (live) testing, or test locally using `sam local invoke`. 

**Package** is the next step if you're gunning to try things out on the Console. The Package command zips all the SAM artifacts, and uploads them to S3. It expands the main SAM template that defines your application, and produces an output template that can be invoked to deploy the application. 
To package the application, do 
`sam package --template-file template.yaml --s3-bucket bucket_name --output-template-file output_file_name.yaml` 

**Deployment** builds the stack, and provisions the resources specified by the packaged template file. To deploy, do 

`sam deploy --template-file ./output_file_name.yaml --stack-name unique-stack-name --capabilities CAPABILITY_NAMED_IAM`

That last bit about `capabilities` is vital. Otherwise, SAM cannot provision the implicit IAM roles that knit Lambdas together, and that stack'll be rolling over before you know it. Also, the cababilities business seems to be a bit wonky. The error messages are typically helpful, and it'll be clear what you need to change or append to the request. 

When you deploy the SAM app, the CLI will hang until it gets an affirmative response from CloudFormation. *This means that you will know if and when the stack has built sucessfully*. 

## Odds and Ends 

If you encounter this 

```bash 
Unable to upload artifact routes/notebooks-get/ referenced by CodeUri parameter of NotebooksGetFunction resource.
An error occurred (ExpiredToken) when calling the PutObject operation: The provided token has expired.
Exception: Command '['aws', 'cloudformation', 'package', '--output-template-file', 'deploy-template.yaml', '--region', 'us-east-2', '--s3-bucket', 'dsp-sam-conv', '--template-file', '/Users/hs/work/dsp-SAM/sam-app/template.yaml']' returned non-zero exit status 255.
```
just renew your CLI credentials. From the SSO, click "programmatic or command line access" and re-export your AWS credentials. There are likely other solutions for this issue, but this is what I did, and it worked. 



