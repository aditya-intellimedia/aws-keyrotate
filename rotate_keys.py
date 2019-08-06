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
    pattern_string = "^\[("+ profile +")?\]\naws_access_key_id = (.*)?\naws_secret_access_key = (.*)"
    pattern = re.compile(pattern_string)
    keys_list = []
    lines = ""

    file_path_expanded = os.path.expanduser(file_path)
    
    if os.path.exists(file_path_expanded):
        fp = open(file_path_expanded, 'r')
        tmp = fp.readline()
        while tmp != "":
            lines += tmp
            tmp = fp.readline()
        try:
            match = re.match(pattern, lines)
            for i in range(1,4):
                keys_list.append(match.group(i))
            print(keys_list)
            #return keys_list
        except AttributeError:
            print("No Keys found for profile %s! Please try again using --profile option" % (profile))
            exit(22)
        fp.close()
    else:
        ## Throw error for file not exists
        print("%s does not exist! Please try again using --path option" % (file_path_expanded))
        exit(22)

def print_version():
    print("AWS Key Rotation Version : %s" % (VERSION))               


## Main line execution

if __name__ == "__main__":
    if args.version:
        print_version()
    else:
        aws_profile = args.profile
        cred_path = args.path
        get_current_keys(cred_path, aws_profile)