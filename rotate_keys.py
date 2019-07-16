#!/usr/bin/env python3

import boto3, os, sys, re
import argparse

## Key Rotation Version
VERSION = "1.0.0"

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--profile', help='The name of the profile to use. Default profile is "default"', type=str, default='default')
parser.add_argument('--path', help='The path for the AWS Credentials file, default is ~/.aws/credentials', type=str, default='~/.aws/credentials')
parser.add_argument('--version', help='Print the version of this program', action='store_true')

args = parser.parse_args()

def get_current_keys(file_path,profile):
    ## Regex pattern for reading creds according to the profile specified
    pattern = re.compile("^\["+ profile +"?\]\naws_access_key_id=(.*)?\naws_secret_access_key=(.*)")
    lines = ""
    keys_list = []

    file_path_expanded = os.path.expanduser(file_path)
    
    if os.path.exists(file_path_expanded):
        with open(file_path_expanded, 'rb') as fp:
            try:
                for line in fp.readlines():
                    buffer += line
                ## Read Credentials
                match = re.match(pattern, buffer)
                
            except:
                ## Handle errors