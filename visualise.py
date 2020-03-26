import re
import os

class Command:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<COMMAND> " + self.name

    def __str__(self):
        return self.name

class ConnectionCommand(Command):

    def __init__(self, name):
        super().__init__(name)
        target_regex = re.compile("- Connect to port (\d+)")
        m = target_regex.search(name)
        self.target = m.group(1)

class InitialConnectCommand(Command):
    pass

class LinkQPUCommand(Command):

    def __init__(self, name):
        super().__init__(name)
        target_regex = re.compile("- Link . QPU to port (\d+)")
        m = target_regex.search(name)
        amount_regex = re.compile("- Link (\d+) QPU")
        n = amount_regex.search(name)
        

        self.target = m.group(1)
        self.amount = n.group(1)
    pass

class BruteForceCommand(Command):
    target_regex = re.compile("- Brute force security system (\d+)")
    pass

class AddNodeToTraceRouteCommand(Command):
    def __init__(self, name):
        super().__init__(name)
        target_regex = re.compile("- Add . nodes to Trace Route (\d+)")
        m = target_regex.search(name)

        amount_regex = re.compile("- Add (\d+) ")
        n = amount_regex.search(name)
        
        self.target = m.group(1)
        self.amount = n.group(1)

class CommandFactory:

    @classmethod
    def createCommandFromText(cls, text):
        link_qpu_regex = re.compile('- Link . QPU to port')
        brute_force_regex = re.compile('- Brute force security system .')
        add_node_to_trace_route_regext = re.compile('- Add . nodes to Trace Route .')
        if text.startswith("- Connect to port"):
            return ConnectionCommand(text)
        elif text.startswith("- Initial connect"):
            return InitialConnectCommand(text)
        elif re.match(link_qpu_regex, text):
            return LinkQPUCommand(text)
        elif re.match(brute_force_regex, text):
            return BruteForceCommand(text)
        elif re.match(add_node_to_trace_route_regext, text):
            return AddNodeToTraceRouteCommand(text)
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






#print([port.getCommands() for port in ports])





def createUML(ports, trace_routes):

    links_to_add = []

    result = ""
    result += "@startuml\n"

    for port in ports:
        port_name = "port%s" % port.index
        result += "object " + port_name + "{\n"
        is_initial_port = False
        for command in port.getCommands():
            result += str(command) + "\n"
            
            if isinstance(command, InitialConnectCommand):
                is_initial_port = True
            elif isinstance(command, ConnectionCommand):
                links_to_add.append((port_name, "port%s" % command.target, "connect", "#red"))
            elif isinstance(command, AddNodeToTraceRouteCommand):
                links_to_add.append((port_name, "traceroute%s" % command.target, "add %s nodes" % command.amount, "#blue"))
            elif isinstance(command, LinkQPUCommand):
                links_to_add.append((port_name, "port%s" % command.target, "Link %s QPU" % command.amount, "#green"))
        
        result += "}\n" 
        if is_initial_port:
            result += "note left: Entry point\n"
    
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