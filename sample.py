# pylint: disable=protected-access
# pylint: disable=invalid-name

"""
This is sample python file for read, write, list and delete vault files.
"""

import sys
import getpass
import argparse
import yaml
from vaultoperation import *


def parse_args():
    """Parse command line args.
    Simple function to parse and return command line args.

    Returns:
        argparse.Namespace: An argparse.Namespace object.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-cfUsername',
                        dest='cfUsername',
                        default=None,
                        required=True,
                        help='Provide Cloud Foundry User Name')
    args = parser.parse_args()
    return args

sourcepath = 'sankartest/vault/'
vaultfile = 'sankartest/vault/testfile.txt'
localfile = 'testfile.txt'


with open('input.yaml', "r") as INPUTF:
    INPUT = yaml.safe_load(INPUTF)


if INPUT['COMMON']:
    api_host = INPUT['COMMON']['cf_api_host']
    login_host = INPUT['COMMON']['cf_login_host']
    proxy_endpoint = INPUT['COMMON']['vault_proxy_url']
    service_instance_name = INPUT['COMMON']['space_vault_name']
    org_name = INPUT['COMMON']['cf_org_name']
    space_name = INPUT['COMMON']['cf_space_name']
else:
    sys.exit("input.yml file is not there. or COMMON list is not defined.")


args = parse_args()
cfUsername = args.cfUsername
print('Enter Ldap password to login Cloud Foundry')
cfPassword = getpass.getpass('Password: ')


def vault_session():
    global secret_manager
    secret_manager = Secrets(username=cfUsername, password=cfPassword, api_host=api_host, login_host=login_host,
                             proxy_endpoint='https://'+proxy_endpoint, service_instance_name=service_instance_name,
                             org_name=org_name, space_name=space_name)
    return secret_manager


def write_vault(wpath, certtarfile):
    secret_manager.delete_file(wpath)
    secret_manager.write_certificate(wpath, certtarfile)


def read_config_vault(cfpath):
    rcvalue = secret_manager.read_data_plain_text(cfpath)
    return rcvalue


def vault_operation_list_dir(wpath):
    listfile = secret_manager.vault_list_path(wpath)
    return listfile


def vault_operation_delete_files(wpath):
    secret_manager.delete_file(wpath)


def main():
    vault_session()
    vault_operation_list_dir(sourcepath)
    read_config_vault(vaultfile)
    write_vault(vaultfile, localfile)



if __name__ == '__main__':
    main()