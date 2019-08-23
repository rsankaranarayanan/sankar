#! /usr/bin/python
# Base64 for encoding and decoding
# Hvac is Hashicorp Vault implementation for creating vault Client without-
#       -storing in filesystem
# pylint: disable=protected-access
# pylint: disable=invalid-name

import base64
import hvac
import subprocess


# noinspection PyShadowingNames,PyShadowingNames
class MyVault:
    def __init__(self):
        """Class for using Vault securely by not storing Vault_Token.
        """
        pass

    @staticmethod
    def create_client(url, roleId, secretId):
        """Method to Create Vault Client using HVAC.

        :param url: Cloud Foundry URL.
        :param roleId: Role ID of Vault
        :param secretId: Secret ID of Vault
        :return: Return Client
        """
        global client
        # global client.token
        client = hvac.Client(url=url)
        longClientToken = client.auth_approle(role_id=roleId, secret_id=secretId)
        client.token = longClientToken['auth']['client_token']
        return client

    @staticmethod
    def client_logout():
        client.logout()

    @staticmethod
    def write_cred(client, path, username, password):
        """Method to write to Vault, i.e. CF username, CF password.
        :param client: HVAC client for Vault
        :param path: Path for Vault
        :param username: Cloud Foundry Username
        :param password: Cloud Foundry Password
        :return:
        """
        client.write(path, CFusername=username,
                     CFpassword=password)

    @staticmethod
    def write_enc_creds(client, proxy, path, data, token):
        """Method to write to Vault, i.e. encrypted credentials.
        :param client: HVAC client for Vault
        :param path: Path for Vault
        :param data: Encrypted data
        :return:
        """
        vault_host = proxy
        curl = 'curl --request POST --header "X-Vault-Token: ' + token + '" --data \'' + data + '\' ' + vault_host + '/v1/' + path
        process = subprocess.Popen(curl, stdout=subprocess.PIPE, stderr=None, shell=True)
        process.communicate()

    @staticmethod
    def enc_creds(client, transit_path, ran_key, input_value):
        """Method to write to Vault, i.e. CF username, CF password.
        :param client: HVAC client for Vault
        :param path: Path for Vault
        :param username: Cloud Foundry Username
        :param password: Cloud Foundry Password
        :return:
        """
        encrypt_data_response = client.transit_encrypt_data(name=ran_key,
                                                            plaintext=base64.urlsafe_b64encode(input_value).decode(
                                                                'ascii'),
                                                            mount_point=transit_path.replace('/encrypt/' + ran_key, ''))
        ciphertext = encrypt_data_response['data']['ciphertext']
        return ciphertext

    @staticmethod
    def write_pub_file(client, path, filepath):
        """ Writes Pub file to vault with Base64 encoding.
        :param client: HVAC client for Vault
        :param path: Path for Vault
        :param filepath: Path to File
        :return:
        """
        with open(filepath, "rb") as f:
            fileEncoded = base64.b64encode(f.read())
            f.close()
            client.write(path,
                         file=fileEncoded)

    @staticmethod
    def write_config_file(client, path, filepath):
        """ Method to write Config file to Vault.

        :param client: HVAC client for Vault
        :param path: Path for Vault
        :param filepath: Path to File
        :return:
        """
        with open(filepath, "rb") as f:
            fileEncoded = base64.b64encode(f.read())
            f.close()
            client.write(path,
                         file=fileEncoded)

    @staticmethod
    def read_cred(client, path, key):
        """ Method to Read Credentials. Note1: Use vault path /secret/cred

        :param client: HVAC client for Vault
        :param path: Path for Vault
        :param key: Enter the Key for which value is stored in Vault
        :return:
        """
        if client.read(path):
            return client.read(path)['data'][key]

    @staticmethod
    def read_pub_file(client, vaultPath, filePath):
        """ Method to Read Public file from Vault & put in given folder.

        :param client: HVAC client for Vault
        :param vaultPath: Path for Vault
        :param filePath: Path for the File
        :return:
        """
        enameValue = client.read(vaultPath)['data']['file']
        decodedValue = base64.b64decode(enameValue)
        with open(filePath, "r+") as f:
            f.write(decodedValue)
            f.close()

    @staticmethod
    def read_config_file(client, vaultPath):
        """ Method to Read Public file from Vault.

        :param client: HVAC client for Vault
        :param vaultPath: Path for Vault
        :return:
        """
        enameValue = client.read(vaultPath)['data']['file']
        decodedValue = base64.b64decode(enameValue)
        return decodedValue

    @staticmethod
    def delete_config_file(client, vaultPath):
        """ Method to Read Public file from Vault.

        :param client: HVAC client for Vault
        :param vaultPath: Path for Vault
        :return:
        """
        enameValue = client.delete(vaultPath)
        return enameValue

    @staticmethod
    def list_file(client, vaultPath):
        """ Method to List file from Vault.

        :param client: HVAC client for Vault
        :param vaultPath: Path for Vault
        :return:
        """
        try:
            enameValue = client.list(vaultPath)['data']['keys']
            return enameValue
        except:
            pass