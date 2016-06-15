#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Create Spark cluster on EMR.

Prompt parameters:
  app               main spark script for submit spark (required)
  app-args:         arguments passed to main spark script
  aws-region:       AWS region name (required)
  cluster-id:       job flow id of existing cluster to submit to
  conf-file:        specify cluster config file
  ec2-key:          name of the Amazon EC2 key pair to use when using SSH
  ec2-subnet-id:    Amazon VPC subnet id
  help (-h):        argparse help
  keep-alive:       Keep EMR cluster alive when no steps
  master:           instance type of of master host (default='m4.large')
  num-nodes:        number of instances (default=1)
  release-label:    EMR release label (required)
  s3-bucket:        name of s3 bucket to upload spark file (required)
  slave:            instance type of of slave hosts (default='m4.2xlarge')
  submit-args:      arguments passed to spark-submit
  sparksteps-conf:  use sparksteps Spark conf
  tags:             EMR cluster tags of the form "key1=value1 key2=value2"
  uploads:          directories to upload to master instance in /home/hadoop/

Examples:
  sparksteps examples/episodes.py \
    --s3-bucket $AWS_S3_BUCKET \
    --aws-region us-east-1 \
    --release-label emr-4.7.0 \
    --uploads examples/lib examples/episodes.avro \
    --submit-args="--jars /home/hadoop/lib/spark-avro_2.10-2.0.2-custom.jar" \
    --app-args="--input /home/hadoop/episodes.avro" \
    --num-nodes 1 \
    --debug

"""
from __future__ import print_function

import argparse
import shlex

import boto3

from sparksteps.steps import setup_steps
from sparksteps.cluster import emr_config


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('app')
    parser.add_argument('--app-args', type=shlex.split)
    parser.add_argument('--aws-region', required=True)
    parser.add_argument('--cluster-id')
    parser.add_argument('--conf-file', metavar='FILE')
    parser.add_argument('--debug', action='store_true')
    parser.add_argument('--ec2-key')
    parser.add_argument('--ec2-subnet-id')
    parser.add_argument('--keep-alive', action='store_true')
    parser.add_argument('--master', default='m4.large')
    parser.add_argument('--num-nodes', type=int, default=1)
    parser.add_argument('--release-label', required=True)
    parser.add_argument('--s3-bucket', required=True)
    parser.add_argument('--slave', default='m4.2xlarge')
    parser.add_argument('--sparksteps-conf', action='store_true')
    parser.add_argument('--submit-args', type=shlex.split)
    parser.add_argument('--tags', nargs='*')
    parser.add_argument('--uploads', nargs='*')

    args = parser.parse_args()

    client = boto3.client('emr', region_name=args.aws_region)
    s3 = boto3.resource('s3')

    cluster_id = args.cluster_id
    if cluster_id is None:  # create cluster
        print("Launching cluster...")
        cluster_config = emr_config(**vars(args))
        response = client.run_job_flow(**cluster_config)
        cluster_id = response['JobFlowId']
        print("Cluster ID: ", cluster_id)

    emr_steps = setup_steps(s3, args.s3_bucket, args.app, args.submit_args,
                            args.app_args, args.uploads)
    client.add_job_flow_steps(JobFlowId=cluster_id, Steps=emr_steps)


if __name__ == '__main__':
    main()
