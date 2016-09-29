
class Router:
    def __init__(self, name, id=None):
        self.name = name
        self.id = id
        self.subnet_names = list()

    def add_subnet(self, subnet_name):
        self.subnet_names.append(subnet_name)

    def get_short_id(self):
        return self.id[:8]

    def __eq__(self, other):
        if self.name == other.name and len(self.subnet_names) == len(other.subnet_names) and \
                                       set(self.subnet_names) == set(other.subnet_names):
            return True
        return False
