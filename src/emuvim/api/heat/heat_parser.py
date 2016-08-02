from __future__ import print_function  # TODO remove when print is no longer needed for debugging
import yaml
import sys
from resources import *


class HeatParser:
    def __init__(self):
        self.description = None
        self.parameter_groups = None
        self.parameters = None
        self.resources = None
        self.outputs = None
        self.bufferResource = list()

    def parse_input(self, input_string, stack):
        yaml_dict = yaml.load(input_string)

        if not (str(yaml_dict['heat_template_version']) == '2015-04-30'):  # TODO: change to versions equal or later then this date (to check that it is a HOT template)
            print('Unsupported template version: ' + yaml_dict['heat_template_version'], file=sys.stderr)
            return

        try:
            self.description = yaml_dict['description']
        except Exception as e:
            self.description = None
            print('No ' + e.message + ' found.')

        try:
            self.parameter_groups = yaml_dict['parameter_groups']
        except Exception as e:
            self.parameter_groups = None
            print('No ' + e.message + ' found.')

        try:
            self.parameters = yaml_dict['parameters']
        except Exception as e:
            self.parameters = None
            print('No ' + e.message + ' found.')

        try:
            self.resources = yaml_dict['resources']
        except Exception as e:
            self.resources = None
            print('No ' + e.message + ' found.')

        try:
            self.outputs = yaml_dict['outputs']
        except Exception as e:
            self.outputs = None
            print('No ' + e.message + ' found.')

        for resource in self.resources:
            self.handle_resource(self.resources[resource], stack)

        # The second for loop tries to create all classes which had unresolved dependencies.
        for resource in self.bufferResource:  # TODO it could be possible that more than one retry is needed (how many?)
            self.handle_resource(resource, stack)

    def handle_resource(self, resource, stack):   # TODO are all resource references complete?
        if "Net" in resource['type']:
            name = resource['properties']['name']
            try:
                if name not in stack.nets:
                    stack.nets[name] = Net(name)
            except Exception as e:
                print('Could not create Net: ' + e.message)
            return

        if 'Subnet' in resource['type'] and "Net" not in resource['type']:
            cidr = resource['properties']['cidr']
            gateway_ip = resource['properties']['gateway_ip']
            name = resource['properties']['name']
            net_name = resource['properties']['network']['get_resource']
            try:
                if net_name not in stack.nets:
                    stack.nets[net_name] = Net(net_name)

                tmp_net = stack.nets[net_name]
                tmp_net.subnet_name = name
                tmp_net.subnet_id = gateway_ip  # TODO maybe this is wrong!? gateway_ip could be something else
                tmp_net.cidr = cidr
            except Exception as e:
                print('Could not create Subnet: ' + e.message)
            return

        if 'Port' in resource['type']:
            network = resource['properties']['network']['get_resource']  # TODO network resource is not stored anywhere
            name = resource['properties']['name']
            try:
                if name not in stack.ports:
                    stack.ports[name] = Port(resource['properties']['name'])
            except Exception as e:
                print('Could not create Port: ' + e.message)
            return

        if 'OS::Nova::Server' in resource['type']:
            compute_name = resource['properties']['name']
            flavor = resource['properties']['flavor']
            nw_list = resource['properties']['networks']  # TODO not used right now
            image = resource['properties']['image']       # TODO not used right now
            command = 'dockerCommand'                     # TODO find out what the command does!!!!!!
            try:
                if compute_name not in stack.servers:
                    stack.servers[compute_name] = Server(compute_name)

                tmp_server = stack.servers[compute_name]
                tmp_server.nw_list = nw_list
                tmp_server.command = command
                tmp_server.image = image
                tmp_server.flavor = flavor
            except Exception as e:
                print('Could not create Server: ' + e.message)
            return

        if 'OS::Neutron::RouterInterface' in resource['type']:
            try:
                router_name = None
                subnet_name = resource['properties']['subnet']['get_resource']

                if 'get_resource' in resource['properties']['router']:
                    router_name = resource['properties']['router']['get_resource']
                else:
                    router_name = resource['properties']['router']

                if router_name not in stack.routers:
                    stack.routers[router_name] = Router(router_name)

                tmp_router = stack.routers[router_name]
                for tmp_net in stack.nets.itervalues():
                    if tmp_net.subnet_name == subnet_name:
                        tmp_router.add_subnet(tmp_net)
                        return
            except Exception as e:
                print('Could not create RouterInterface: ' + e.__repr__())
            print('Could not create RouterInterface, because Net-Class was not found. Maybe it does not exist now.')
            self.bufferResource.append(resource)
            return

        if 'OS::Neutron::FloatingIP' in resource['type']:
            try:
                port_id = resource['properties']['port_id']['get_resource']
                floating_network_id = resource['properties']['floating_network_id']
                if port_id not in stack.ports:
                    stack.ports[port_id] = Port(port_id)

                tmp_port = stack.ports[port_id]
                tmp_port.floating_ip = floating_network_id
            except Exception as e:
                print('Could not create FloatingIP: ' + e.message)
            return

        if 'OS::Neutron::Router' in resource['type'] and 'RouterInterface' not in resource['type']: #TODO find a better way to isolate Router from RouterInterface
            try:
                name = resource['properties']['name']
                if name not in stack.routers:
                    stack.routers[name] = Router(name)
            except Exception as e:
                print('Could not create Router: ' + e.message)
            return




if __name__ == '__main__':
    inputFile = open('yamlTest2', 'r')
    inp = inputFile.read()
    inputFile.close()
    stack = Stack()
    x = HeatParser()
    x.parse_input(inp, stack)
