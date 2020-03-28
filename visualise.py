import re
import os

class Command:
    def __init__(self, name):
        self.name = name
        self._target_regex = None
        self._amount_regex = None
        self._origin_regex = None
        self._target = None
        self._amount = None
        self._origin = None

    def __repr__(self):
        return "<COMMAND> " + self.name

    def __str__(self):
        return self.name

    @property
    def target(self):
        if self._target is None and self._target_regex is not None:
            m = self._target_regex.search(self.name)
            self._target = m.group(1)

        return self._target

    @property
    def amount(self):
        if self._amount is None and self._amount_regex is not None:
            m = self._amount_regex.search(self.name)
            self._amount = m.group(1)

        return self._amount

    @property
    def origin(self):
        if self._origin is None and self._origin_regex is not None:
            m = self._origin_regex.search(self.name)
            self._origin = m.group(1)

        return self._origin


class ConnectionCommand(Command):
    def __init__(self, name):
        super().__init__(name)
        self._target_regex = re.compile(". Connect to port (\d+)")

class InitialConnectCommand(Command):
    pass

class LinkQPUCommand(Command):

    def __init__(self, name):
        super().__init__(name)
        self._target_regex = re.compile(". Link . QPU to port (\d+)")
        self._amount_regex = re.compile(". Link (\d+) QPU")

class BruteForceCommand(Command):
    def __init__(self, name):
        super().__init__(name)
        self._target_regex = re.compile(". Brute force security system (\d+)")


class AddNodeToTraceRouteCommand(Command):
    def __init__(self, name):
        super().__init__(name)
        self._target_regex = re.compile(". Add . nodes to Trace Route (\d+)")

        self._amount_regex = re.compile(". Add (\d+) ")


class RedirectQPUCommand(Command):
    def __init__(self, name):
        super().__init__(name)
        self._target_regex = re.compile(". Redirect up to . QPU from port . to port (\d+)")
        self._amount_regex = re.compile(". Redirect up to (\d+)")
        self._origin_regex = re.compile(". Redirect up to . QPU from port (\d+)")


class CommandFactory:

    @classmethod
    def createCommandFromText(cls, text):
        link_qpu_regex = re.compile('. Link . QPU to port')
        brute_force_regex = re.compile('. Brute force security system .')
        add_node_to_trace_route_regext = re.compile('. Add . nodes to Trace Route .')
        connect_to_port_regex = re.compile(". Connect to port")
        initial_connect_regex = re.compile(". Initial connect")
        redirect_qpu_regex = re.compile(". Redirect up to . QPU from port .")
        if re.match(connect_to_port_regex, text):
            return ConnectionCommand(text)
        elif re.match(initial_connect_regex, text):
            return InitialConnectCommand(text)
        elif re.match(link_qpu_regex, text):
            return LinkQPUCommand(text)
        elif re.match(brute_force_regex, text):
            return BruteForceCommand(text)
        elif re.match(add_node_to_trace_route_regext, text):
            return AddNodeToTraceRouteCommand(text)
        elif re.match(redirect_qpu_regex, text):
            return RedirectQPUCommand(text)
        return Command(text)    


class TraceRoute:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<TraceRoute> " + self.name

    def __str__(self):
        return self.name


class Port:
    def __init__(self, idx):
        self._commands = []
        self.index = idx

    def addCommandFromText(self, text):
        self._commands.append(CommandFactory.createCommandFromText(text))

    def getCommands(self):
        return self._commands


with open("sample_server.txt") as f:
    data = f.read()


ports = []

trace_routes = []

port_number = 0
active_port = None
trace_route_regex = re.compile("Nodes in trace route . at the start")

for idx, line in enumerate(data.split("\n")):
    
    if line.startswith("Port"):
        port_number += 1
        active_port = Port(port_number)
        ports.append(active_port)
        continue

    if line == "":
        active_port = None # Whitespace means we're not in a node anymore, stfu
        continue

    if re.match(trace_route_regex, line):
        trace_routes.append(TraceRoute(line))
        continue
    active_port.addCommandFromText(line)


def createUML(ports, trace_routes):

    links_to_add = []

    result = ""
    result += "@startuml\n"
    result += "skinparam backgroundColor #000000\n"
    result += "skinparam objectBackgroundColor #000000\n"
    result += "skinparam defaultFontColor green\n"
    result += "skinparam objectBorderColor green\n"
    result += "skinparam objectFontSize 17\n"
    result += "skinparam shadowing false\n"

    ##result +=

    for port in ports:
        port_name = "Port_%s" % port.index

        is_initial_port = False
        for command in port.getCommands():
            if isinstance(command, InitialConnectCommand):
                is_initial_port = True
                break
        if is_initial_port:
            result += "object " + port_name + " <<ENTRY POINT>> {\n"
        else:
            result += "object " + port_name + " {\n"

        for command in port.getCommands():
            result += str(command) + "\n"

            if isinstance(command, ConnectionCommand):
                links_to_add.append((port_name, "Port_%s" % command.target, "Connect", "#red"))
            elif isinstance(command, AddNodeToTraceRouteCommand):
                links_to_add.append((port_name, "traceroute%s" % command.target, "add %s nodes" % command.amount, "#blue"))
            elif isinstance(command, LinkQPUCommand):
                links_to_add.append((port_name, "Port_%s" % command.target, "Link %s QPU" % command.amount, "#green"))
            elif isinstance(command, RedirectQPUCommand):
                text = ""
                if "Port_%s" % command.origin != port_name:
                    text = "Redirect %s QPU (from Port %s)" % (command.amount, command.origin)
                else:
                    text = "Redirect %s QPU" % command.amount

                links_to_add.append((port_name, "Port_%s" % command.target, text, "#green"))
        
        result += "}\n"
    
    for trace_route in trace_routes:
        trace_route_index = trace_route.name.partition("Nodes in trace route ")[2][:1]
        result += "object traceroute" + trace_route_index + "{\n"
        result += "}\n"

    for link in links_to_add:
        result += link[0] + " -[%s]-|> " % link[3] + link[1] + " : " + link[2] + "\n"

    result += "@enduml"
    return result


with open("result.txt", "w") as f:
    f.write(createUML(ports, trace_routes))

os.system("java -jar plantuml.jar result.txt")


#
#print(data)