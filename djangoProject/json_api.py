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

import json
import sys
from json.decoder import JSONDecodeError

# -----------------------------------------------------------------------------------
# Objects to describe a tree hierarchy used in output_tree.html
# -----------------------------------------------------------------------------------
class TreeEntry():

    def __init__(self, start_list, end_list, with_children, key, value):
        self.start_list = start_list     # Start a new list before the print
        self.end_list = end_list          # end aa list after the print
        self.with_children = with_children    # With children attributes
        self.key = key
        self.value = value

# -----------------------------------------------------------------------------------
# String to JSON
# -----------------------------------------------------------------------------------
def string_to_json( data_str ):

    try:
        #json_struct = data_str.json()
        json_struct = json.loads(data_str)
    except ValueError as err:
        error_msg = "Failed to map string to JSON: %s" % str(err)
        json_struct = None
    except JSONDecodeError as err:
        error_msg = "Failed to map string to JSON: %s" % str(err)
        json_struct = None
    except KeyError as err:
        error_msg = "Failed to map string to JSON: %s" % str(err)
        json_struct = None
    except:
        errno, err = sys.exc_info()[:2]
        error_msg = "Failed to map string to JSON: %s" % str(err)
        json_struct = None
    else:
        error_msg = None

    return [json_struct, error_msg]

# -----------------------------------------------------------------------------------
# JSON to string
# -----------------------------------------------------------------------------------
def json_to_string(json_struct):

    try:
        data_str = json.dumps(json_struct)
    except ValueError as err:
        error_msg = "Failed to map JSON to string: %s" % str(err)
        data_str = None
    except JSONDecodeError as err:
        error_msg = "Failed to map JSON to string: %s" % str(err)
        data_str = None
    except:
        error_msg = "Failed to map JSON to string"
        data_str = None
    else:
        error_msg = None

    return [data_str, error_msg]
# =======================================================================================================================
# String to list
# =======================================================================================================================
def string_to_list(data: str):

    try:
        list_obj = list(eval(data))
    except:
        errno, value = sys.exc_info()[:2]
        list_obj = None
        sys_error = str(value)
        if "true" in sys_error or "false" in sys_error:
            # Python needs True/False capitalized
            updated_data = data.replace("true", "True").replace("false","False")
            try:
                list_obj = list(eval(updated_data))
            except:
                errno, value = sys.exc_info()[:2]
        if not list_obj:
            error_msg = f"Failed to map List to string: {value}"
        else:
            error_msg = None
    else:
        error_msg = None

    return [list_obj, error_msg]

# -----------------------------------------------------------------------------------
# Simple setup of a print of a list of JSON policies
# Send structure to output.html
# -----------------------------------------------------------------------------------
def simple_polisies_list(policies):
    data_list = []
    for json_entry in policies:
        json_string = json.dumps(json_entry,indent=4, separators=(',', ': '), sort_keys=True)
        data_list.append(json_string)  #  transformed to a JSON string.
    return data_list

# -----------------------------------------------------------------------------------
# Print setup of JSON for output_tree.html
# -----------------------------------------------------------------------------------
def setup_print_tree( source_struct, print_struct ):

    if isinstance(source_struct, dict):

        counter = len(source_struct) - 1  # The number of entries
        index = 0

        new_entry = TreeEntry(True, False, False, None, None)  # Start List
        print_struct.append(new_entry)
        for key, value in source_struct.items():

            if isinstance(value,list) or isinstance(value, dict):
                start_list = not counter
                end_list = counter == index
                new_entry = TreeEntry(False, False, True, key, None)
                print_struct.append(new_entry)
                setup_print_tree( value, print_struct )
            else:
                set_edge(key, value, print_struct )

            index += 1

        new_entry = TreeEntry(False, True, False, None, None) # End List
        print_struct.append(new_entry)

    elif isinstance(source_struct, list):
        counter = len(source_struct) - 1  # The number of entries

        for index, entry in enumerate(source_struct):

            if isinstance(entry, list) or isinstance(entry, dict):
                start_list = not counter
                end_list = counter == index
                setup_print_tree(entry, print_struct)
            else:
                set_edge(None, entry, print_struct)

    else:
        set_edge(None, source_struct, print_struct)


# -----------------------------------------------------------------------------------
# Add edge Node
# -----------------------------------------------------------------------------------
def set_edge(key, value, print_struct):

    if key:
        data = str(key) + " : " + str(value)
    else:
        data = str(value)

    new_entry = TreeEntry(False, False, False, key, value)
    print_struct.append(new_entry)

# ------------------------------------------------------------------------
# The process to load a JSON file that maintanins the GUI view of the data/metadata
# ------------------------------------------------------------------------
def load_json(file_name):

    try:
        f = open(file_name)
        data = json.load(f)
    except JSONDecodeError as e:
        data = None
        error_msg = "AnyLog: Config File format error - line: {} column: {} message: {}".format(e.lineno, e.colno, e.msg)
    except:
        errno, value = sys.exc_info()[:2]
        error_msg = "AnyLog: Failed to load file: '%s' with error: %s" % (file_name, str(value))
        data = None
    else:
        error_msg = None
    return [data, error_msg]