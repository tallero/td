#
# Copyright Aliaksei Levin (levlam@telegram.org), Arseny Smirnov (arseny30@gmail.com),
# Pellegrino Prevete (pellegrinoprevete@gmail.com)  2014-2018
#
# Distributed under the Boost Software License, Version 1.0. (See accompanying
# file LICENSE_1_0.txt or copy at http://www.boost.org/LICENSE_1_0.txt)
#
from ctypes.util import find_library
from ctypes import *
import json
import sys

# load shared library
tdjson_path = find_library("tdjson") or "tdjson.dll"
if tdjson_path is None:
    print('can\'t find tdjson library')
    quit()
tdjson = CDLL(tdjson_path)

# load TDLib functions from shared library
td_json_client_create = tdjson.td_json_client_create
td_json_client_create.restype = c_void_p
td_json_client_create.argtypes = []

td_json_client_receive = tdjson.td_json_client_receive
td_json_client_receive.restype = c_char_p
td_json_client_receive.argtypes = [c_void_p, c_double]

td_json_client_send = tdjson.td_json_client_send
td_json_client_send.restype = None
td_json_client_send.argtypes = [c_void_p, c_char_p]

td_json_client_execute = tdjson.td_json_client_execute
td_json_client_execute.restype = c_char_p
td_json_client_execute.argtypes = [c_void_p, c_char_p]

td_json_client_destroy = tdjson.td_json_client_destroy
td_json_client_destroy.restype = None
td_json_client_destroy.argtypes = [c_void_p]

td_set_log_file_path = tdjson.td_set_log_file_path
td_set_log_file_path.restype = c_int
td_set_log_file_path.argtypes = [c_char_p]

td_set_log_max_file_size = tdjson.td_set_log_max_file_size
td_set_log_max_file_size.restype = None
td_set_log_max_file_size.argtypes = [c_longlong]

td_set_log_verbosity_level = tdjson.td_set_log_verbosity_level
td_set_log_verbosity_level.restype = None
td_set_log_verbosity_level.argtypes = [c_int]

fatal_error_callback_type = CFUNCTYPE(None, c_char_p)

td_set_log_fatal_error_callback = tdjson.td_set_log_fatal_error_callback
td_set_log_fatal_error_callback.restype = None
td_set_log_fatal_error_callback.argtypes = [fatal_error_callback_type]

# initialize TDLib log with desired parameters
def on_fatal_error_callback(error_message):
    print('TDLib fatal error: ', error_message)

td_set_log_verbosity_level(2)
c_on_fatal_error_callback = fatal_error_callback_type(on_fatal_error_callback)
td_set_log_fatal_error_callback(c_on_fatal_error_callback)

# create client
client = td_json_client_create()

# simple wrappers for client usage
def td_send(query):
    query = json.dumps(query).encode('utf-8')
    td_json_client_send(client, query)

def td_receive():
    result = td_json_client_receive(client, 1.0)
    if result:
        result = json.loads(result.decode('utf-8'))
    return result

def td_execute(query):
    query = json.dumps(query).encode('utf-8')
    result = td_json_client_execute(client, query)
    if result:
        result = json.loads(result.decode('utf-8'))
    return result

# testing TDLib execute method
print(td_execute({'@type': 'getTextEntities', 'text': '@telegram /test_command https://telegram.org telegram.me', '@extra': ['5', 7.0]}))

# testing TDLib send method
td_send({'@type': 'getAuthorizationState', '@extra': 1.01234})

# main events cycle
while True:
    event = td_receive()
    if event:
        # process authorization states
        if event['@type'] == 'updateAuthorizationState'
            auth_state = event['authorization_state']
            
            # if client is closed, we need to destroy it and create new client
            if auth_state['@type'] == 'authorizationStateClosed':
            break

            # set tdlib parameters
            if auth_state['@type'] == 'authorizationStateWaitTdlibParameters':
                td_send({'@type':"setTdlibParameters", "parameters":{
                                                       "database_directory":"tdlib",
                                                       "use_message_database":True,
                                                       "use_secret_chats":True,
                                                       "api_id":"your_api_id",
                                                       "api_hash":"your_api_hash",
                                                       "system_language_code":"en",
                                                       "device_model":"Desktop",
                                                       "system_version":"Linux",
                                                       "application_version":"1.0",
                                                       "enable_storage_optimizer":True}})

            # set an encryption key for database to let know tdlib how to open the database
            if auth_state['@type'] == 'authorizationStateWaitEncryptionKey':
                td_send({"@type":"checkDatabaseEncryptionKey", "key":"my_key"})

            # insert phone number for login
            if auth_state['@type'] == "authorizationStateWaitPhoneNumber":
                phone_number = input("Please insert your phone number: ")
                td_send({"@type":"setAuthenticationPhoneNumber", "phone_number":phone_number})

            # wait for authorization code
            if auth_state['@type'] == 'authorizationStateWaitCode':
                code = input("Please insert the authentication code you received: ")
                td_send({"@type":"checkAuthenticationCode", "code":code})

            # wait for password if present
            if auth_state['@type'] == "authorizationStateWaitPassword":
                password = input("Please insert your password: ")
                td_send({"@type":"checkAuthenticationPassword", "password":password})

        # handle an incoming update or an answer to a previously sent request
        print(event)
        sys.stdout.flush()

# destroy client when it is closed and isn't needed anymore
td_json_client_destroy(client)
