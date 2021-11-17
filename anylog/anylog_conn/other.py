def error_message(conn:str, command_type:str, error_type:str, error_msg:str)->str:
    """
    Return error message based on arguments provided by user
    :args:
        conn:str - REST connection information
        command_type:str - Type of command executed [ex. GET, PUT, POST]
        error_type:str - Type of error message [ex. Network, formatting, other]
        error_msg:str - Error from exception message
    :return:
        full error message
    """
    if error_type == 'network':
        return "Failed to execute %s against '%s' (Network Error: %s)" % (command_type, conn, error_msg)
    elif error_type == 'formatting':
        return "Failed to format %s results against '%s' (Error: %s)" % (command_type, conn, error_msg)
    else:
        return "Failed to execute %s against '%s' (Error: %s)" % (command_type, conn, error_msg)

