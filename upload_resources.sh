#!/bin/bash

# $1 is core-src bucket name, $2 is emr bucket name 
# uploads CloudFormation templates and EMR scripts to S3 
echo "[[INFO]] Bucket creation complete!"
echo "Initializing object upload"

aws s3 sync ./template-resources $1 --exclude ".DS*" 
echo "[[INFO]] Template upload complete!"
aws s3 sync ./emr-resources $2 --exclude ".DS*"
echo "[[INFO]] EMR Script upload complete!"


