#!/usr/bin/env python3

import boto3, os, sys, re
import argparse
from botocore.exceptions import ClientError

## Key Rotation Version
VERSION = "1.0.5"

parser = argparse.ArgumentParser()
parser.add_argument('--profile', help='The name of the profile to use. Default is "default"', type=str, default='default')
parser.add_argument('--path', help='The path for the AWS Credentials file. Default is ~/.aws/credentials', type=str, default='~/.aws/credentials')
parser.add_argument('--username', help='The name of the IAM user. Default is empty.', type=str, default='')
parser.add_argument('--access-key', help='The Access Key of the user you would like to delete. Default will be the keys used from the profile', type=str, default='')
parser.add_argument('--version', help='Print the version of this program', action='store_true')

args = parser.parse_args()

def get_current_keys(file_path,profile):
    ## Regex pattern for reading creds according to the profile specified
    pattern_string = "^\[("+ profile +")?\]\naws_access_key_id = (.*)?\naws_secret_access_key = (.*)"
    pattern = re.compile(pattern_string, re.MULTILINE)
    keys_list = []
    lines = ""

    file_path_expanded = os.path.expanduser(file_path)
    
    if os.path.exists(file_path_expanded):
        fp = open(file_path_expanded, 'r')
        lines = fp.read()
        try:
            match = re.search(pattern, lines)
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
def rotate_keys(keys_list,username, tgt_access_key):
    new_keys_list = []
    current_user = username
    access_key_id = keys_list[0]
    secret_access_key = keys_list[1]
    try:
        session = boto3.Session(
            aws_access_key_id = access_key_id,
            aws_secret_access_key = secret_access_key
        )
        # Get IAM Client & Resource
        iam_client = session.client('iam')
        iam_resource = session.resource('iam')
        current_iam_user = iam_resource.CurrentUser().user_name
        if current_user == "":
            current_user = iam_resource.CurrentUser().user_name
        print("Performing Key rotation for IAM User: %s" % (current_user))
        
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

        # Delete the access key (target Key/Current Key)
        cur_access_key = tgt_access_key
        if tgt_access_key == "":
            cur_access_key = access_key_id

        iam_client.delete_access_key(UserName=current_user, AccessKeyId=cur_access_key)
        print("Access Key %s has been deleted." % (cur_access_key))
        new_keys_metadata = iam_client.create_access_key(UserName=current_user)['AccessKey']
        new_keys_list.append(current_iam_user)
        new_keys_list.append(new_keys_metadata['AccessKeyId'])
        new_keys_list.append(new_keys_metadata['SecretAccessKey'])
        return new_keys_list
    except ClientError as e:
        error_obj = e.response['Error']
        if error_obj['Code'] == 'InvalidClientTokenId':
            print("The credentials provided are invalid! Please try again.")
            exit(1)
        else:
            print(error_obj['Code'] + " : " + error_obj['Message'])
            exit(1)

def print_version():
    print("AWS Key Rotation Version : %s" % (VERSION))

def replace_keys_in_file(old_creds, new_creds, filepath):
    filepath_expanded = os.path.expanduser(filepath)
    lines = ""
    if os.path.exists(filepath_expanded):
        fp = open(filepath_expanded, 'r')
        lines = fp.read()
        for i in range(0,len(old_creds)):
            lines = lines.replace(old_creds[i], new_creds[i])
        fp.close()
        fp = open(filepath_expanded, 'w+')
        fp.write(lines)
        fp.close()
        print("Credentials have been written successfully in %s" % (filepath_expanded))

## Main line execution

if __name__ == "__main__":
    if args.username and (args.access_key == ""):
        parser.error("--username requires --access-key.")
    if args.version:
        print_version()
    else:
        aws_profile = args.profile
        cred_path = args.path
        username = args.username
        target_access_key = args.access_key
        old_keys = get_current_keys(cred_path, aws_profile)
        new_keys = rotate_keys(old_keys, username, target_access_key)
        fmt_string = '''
Your new access & secret keys have been generated successfully.

----------------------------------
IAM User : {0}
New AWS Access Key {1}
New AWS Secret Key = {2}
----------------------------------
        '''
        fmt_user = username
        if username == "":
            fmt_user = new_keys[0]
        print(fmt_string.format(fmt_user, new_keys[1], new_keys[2]))
        if username != "":
            iam_user = new_keys[0]
            if username != iam_user:
                print("Username is different when compared to IAM user. Not writing credentials to the file.")
            else:
                new_keys = new_keys[1:]
                replace_keys_in_file(old_keys, new_keys, cred_path)
        else:
            # Replace the keys in the file
            new_keys = new_keys[1:]
            replace_keys_in_file(old_keys, new_keys, cred_path)