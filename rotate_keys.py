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
            for i in range(2,4):
                keys_list.append(match.group(i))
            return keys_list
        except AttributeError:
            print("No Keys found for profile %s! Please try again using --profile option" % (profile))
            exit(22)
        fp.close()
    else:
        ## Throw error for file not exists
        print("%s does not exist! Please try again using --path option" % (file_path_expanded))
        exit(22)

# Method for performing actual rotation of the keys
def rotate_keys(keys_list):
    new_keys_list = []

    access_key_id = keys_list[0]
    secret_access_key = keys_list[1]
    session = boto3.Session(
        aws_access_key_id = access_key_id,
        aws_secret_access_key = secret_access_key
    )
    # Get IAM Client & Resource
    iam_client = session.client('iam')
    iam_resource = session.resource('iam')
    current_user = iam.CurrentUser().user_name
    print("Performing Key rotation for IAM User : %s" % (current_user))
    
    # Get the list of access keys for the user
    access_keys_list = iam_client.list_access_keys(UserName=current_user)
    active_keys = 0
    inactive_keys = 0
    for key in access_keys_list['AccessKeyMetadata']:
        if key['Status'] == 'Inactive': inactive_keys += 1
        elif key['Status'] == 'Active': active_keys += 1
    print("#######################################")
    print("User Name: %s" % (current_user))
    print("Active Keys: %d" % (active_keys))
    print("Inactive Keys: %d " % (inactive_keys))
    print("#######################################")

    # Delete the current access key
    iam_client.delete_access_key(UserName=current_user, AccessKeyId=access_key_id)
    print("Access Key %s has been deleted." % (access_key_id))
    new_keys_metadata = iam_client.create_access_key(UserName=current_user)['AccessKey']
    new_keys_list.append(new_keys_metadata['AccessKeyId'])
    new_keys_list.append(new_keys_metadata['SecretAccessKey'])
    return new_keys_list

def print_version():
    print("AWS Key Rotation Version : %s" % (VERSION))               

## Main line execution

if __name__ == "__main__":
    if args.version:
        print_version()
    else:
        aws_profile = args.profile
        cred_path = args.path
        old_keys = get_current_keys(cred_path, aws_profile)
        new_keys = rotate_keys(old_keys)
        fmt_string = '''
        Your new access & secret keys have been generated successfully.
        Please find the same:
        [{0}]
        aws_access_key_id = {1}
        aws_secret_access_key = {2}
        '''
        print(fmt_string.format(aws_profile, new_keys[0], new_keys[1]))