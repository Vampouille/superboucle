def client_registration_callback(name, register):
    print('client_registration: %s %s' % (name, register))


def port_registration_callback(port, register):
    print('port_registration: %s %s' % (port, register))


def port_connect_callback(portFrom, portTo, register):
    print('port_connect: %s -> %s %s' % (portFrom, portTo, register))


def port_rename_callback(port, old, new):
    print('port_rename: %s %s -> %s' % (port, old, new))


def graph_order_callback():
    print('graph_order')


def xrun_callback(delayed_usecs):
    print('xrun: %sus')


def property_change_callback(*args):
    print('property_change: %s ' % (args))
