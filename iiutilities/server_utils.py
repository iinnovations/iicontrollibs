#!/usr/bin/python3

__author__ = 'Colin Reese'
__copyright__ = 'Copyright 2016, Interface Innovations'
__credits__ = ['Colin Reese']
__license__ = 'Apache 2.0'
__version__ = '1.0'
__maintainer__ = 'Colin Reese'
__email__ = 'support@interfaceinnovations.org'
__status__ = 'Development'


def get_hpacucli_status(device_label):

    status = 5 # NOT FOUND
    from subprocess import run, PIPE
    result = run(['hpacucli', 'ctrl', 'all', 'show', 'config'], stdout=PIPE)
    text_result = result.stdout
    text_lines = text_result.split(b'\n')
    for line in text_lines:
        if device_label in str(line):
            # print(line)
            if 'OK' in str(line):
                status = 0 # OK
            else:
                status  = 1

    return status


def get_cpu_usage(**kwargs):
    import psutil
    return {'percent': psutil.cpu_percent()}


def get_disk_usage(mountpoints=all):
    import psutil
    partitions = psutil.disk_partitions()

    if mountpoints == 'all':
        du_mountpoints = [p.mountpoint for p in partitions]
    elif isinstance(mountpoints, str):
        du_mountpoints = [mountpoints]
    elif isinstance(mountpoints, list):
        pass
    else:
        return {'value':-1, 'status':1, 'message':'mountpoint of wrong type, type {}'.format(type(mountpoints))}

    return_dict = {}
    for mountpoint_name in du_mountpoints:
        return_dict[mountpoint_name] = {}
        this_item = return_dict[mountpoint_name]
        for p in partitions:
            if mountpoint_name == p.mountpoint:
                this_item['usage'] = psutil.disk_usage(mountpoint_name)

    print('disk usage for {}'.format(du_mountpoints))
    print(return_dict)
    return return_dict


def get_memory_usage(**kwargs):
    settings = {}
    settings.update(kwargs)
    import psutil
    memory_usage = psutil.virtual_memory()
    return memory_usage


def get_network_health():
    pass
