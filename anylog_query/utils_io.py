'''
By using this source code, you acknowledge that this software in source code form remains a confidential information of AnyLog, Inc.,
and you shall not transfer it to any other party without AnyLog, Inc.'s prior written consent. You further acknowledge that all right,
title and interest in and to this source code, and any copies and/or derivatives thereof and all documentation, which describes
and/or composes such source code or any such derivatives, shall remain the sole and exclusive property of AnyLog, Inc.,
and you shall not edit, reverse engineer, copy, emulate, create derivatives of, compile or decompile or otherwise tamper or modify
this source code in any way, or allow others to do so. In the event of any such editing, reverse engineering, copying, emulation,
creation of derivative, compilation, decompilation, tampering or modification of this source code by you, or any of your affiliates (term
to be broadly interpreted) you or your such affiliates shall unconditionally assign and transfer any intellectual property created by any
such non-permitted act to AnyLog, Inc.
'''

import sys
import os
import shutil

def get_files_in_dir(path, size_flag):
    '''
    Return the list of files:
    path - path to directory
    size_flag - if True - returns a list of lists - every list include file name + size
    '''

    files_info = []
    try:
        files_list = os.listdir(path)
    except:
        files_list = None
    else:
        for file_name in files_list:
            if  size_flag:
                try:
                    file_size = os.path.getsize(path + file_name)
                except:
                    file_size = 0
            else:
                file_size = 0
            files_info.append([file_name, file_size])


    return files_info

def delete_file( file_path_name ):
    ret_val = True

    try:
        os.remove(file_path_name)
    except:
        ret_val = False

    return ret_val


def copy_file(des_file, source_file):

    ret_val = True

    try:
        shutil.copyfile(source_file, des_file)
    except:
        ret_val = False

    return ret_val

def read_file(file_name):
    '''
    file_name - pathe + file name
    '''

    try:
        with open(file_name) as f:
            data = f.read()
    except:
        errno, value = sys.exc_info()[:2]
        data = None

    return data