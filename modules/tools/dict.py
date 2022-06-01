def get_logged_app_parameter_if_exists(parameter_dict, parameter_name):
    parameter_value = None
    if parameter_name in parameter_dict:
        parameter_value = parameter_dict[parameter_name]
        log.info(" " + parameter_name + ": " + str(parameter_value))
    return parameter_value


def replace_key_in_dict(dict, key, replace_object):
    if key in dict.keys():
        del dict[key]
    dict[key] = replace_object
