#! /usr/bin/python
"""This python script is wrapper script for vault operations like write, read, list and delete action.
"""
# pylint: disable=protected-access
# pylint: disable=invalid-name

from __future__ import print_function
import sys
from cloudfoundryapi import CfApi
from MyVault import *


class Secrets:
    def __init__(self, **kwargs):
        self.api_host = kwargs.get('api_host', '')
        self.login_host = kwargs.get('login_host', '')
        self.username = kwargs.get('username', '')
        self.password = kwargs.get('password', '')
        self.org_name = kwargs.get('org_name', '')
        self.space_name = kwargs.get('space_name', '')
        self.proxy_endpoint = kwargs.get('proxy_endpoint', '')
        self.service_instance_name = kwargs.get('service_instance_name', '')
        cfapi = CfApi(username=self.username, password=self.password, login_host=self.login_host,
                      api_host=self.api_host, org_name=self.org_name, space_name=self.space_name)
        servicecheck = cfapi.verify_servicename(self.service_instance_name)
        if servicecheck:
            vaultsecrets = cfapi.get_service_credentials(self.service_instance_name)
        else:
            sys.exit("{0} vault instances is not available.".format(self.service_instance_name))
        for vinfo in vaultsecrets['resources']:
            role_id = vinfo['entity']['credentials']['role_id']
            secret_id = vinfo['entity']['credentials']['secret_id']
            self.service_secret_path = vinfo['entity']['credentials']['service_secret_path'].strip('v1/')
        self.vault_client = MyVault.create_client(self.proxy_endpoint, roleId=role_id, secretId=secret_id)

    def iterative(self, spath=None, parentlist=None):
        if spath:
            if parentlist is None:
                parentlist = []
            value = MyVault.list_file(self.vault_client, self.service_secret_path + "/" + spath)
            if value and isinstance(value, list):
                for v in value:
                    conpath = spath.encode('utf-8') + "/" + v
                    parentlist.append(conpath.replace("//", "/"))
                    self.iterative(conpath, parentlist)
            return parentlist
        else:
            value = MyVault.list_file(self.vault_client, self.service_secret_path)
            return value

    def vault_list_path(self, spath=None):
        if spath:
            retvalue = []
            value = self.iterative(spath)
            if value:
                for v in value:
                    if not v.endswith("/"):
                        retvalue.append(v)
                return retvalue
            else:
                print("{0} path is in-valid or {0} is file. please provide right directory instead of file.".format(spath))
        else:
            return self.iterative()

    def write_enc_creds(self, path, data):
        MyVault.write_enc_creds(self.vault_client, self.proxy_endpoint, self.service_secret_path + "/" + path,
                                data, self.vault_client.token)

    def read_data_enc_mode(self, path, key):
        cred_val = MyVault.read_cred(self.vault_client, self.service_secret_path + "/" + path, key)
        return cred_val

    def delete_file(self, dpath):
        MyVault.delete_config_file(self.vault_client, self.service_secret_path + "/" + dpath)

    def download_file(self, path, sfile):
        cred_val = MyVault.read_pub_file(self.vault_client, self.service_secret_path + "/" + path, sfile)
        return cred_val

    def write_certificate(self, path, sfile):
        MyVault.write_config_file(self.vault_client, self.service_secret_path + "/" + path, sfile)

    def read_data_plain_text(self, spath):
        value = MyVault.read_config_file(self.vault_client, self.service_secret_path + "/" + spath)
        return value

    def client_logout(self):
        MyVault.client_logout()
