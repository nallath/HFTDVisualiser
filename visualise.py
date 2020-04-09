import re
import os


from Commands import CommandFactory
from Commands import InitialConnectCommand, BruteForceCommand, AddNodeToTraceRouteCommand

class TraceRoute:
    def __init__(self, line):
        self._line = line
        self._system_number_regex = re.compile("Nodes in trace route (\d+)|Trace Route (\d+)")
        match = re.match(self._system_number_regex, line)
        if match.group(1) is not None:
            trace_route_number = match.group(1)
        else:
            trace_route_number = match.group(2)
        self._name = "Traceroute_%s" % trace_route_number

    def __repr__(self):
        return "<TraceRoute> " + self.name

    def __str__(self):
        return self.name

    @property
    def name(self):
        return self._name


class SecuritySystem:
    def __init__(self, line):
        self._line = line
        self._system_number_regex = re.compile("^(\-|>)?\s*Brute [Ff]orce [sS]ecurity [sS]ystem (\d+)")
        m = self._system_number_regex.search(self._line)
        self._name = "SecuritySystem_%s" % m.group(2)

    @property
    def name(self):
        return self._name

    def __str__(self):
        return self._name

    def __hash__(self):
        return hash(self._name)

    def __repr__(self):
        return "<SecuritySystem> " + self.name

    def __eq__(self, other):
        return self.name == other.name


class Port:
    def __init__(self, idx):
        self._commands = []
        self.index = idx

    def addCommandFromText(self, text):
        results = CommandFactory.createCommandFromText(text)
        if isinstance(results, list):
            for result in results:
                result.setPort(self)
            self._commands.extend(results)
        else:
            results.setPort(self)
            self._commands.append(results)

    def getCommands(self):
        return self._commands


with open("sample_server.txt") as f:
    data = f.read()


ports = []

trace_routes = []

security_systems = set()

port_number = 0
active_port = None
trace_route_regex = re.compile("Nodes in trace route .|Trace Route .")
security_system_regex = re.compile("^(\-|>)?\s*Brute [fF]orce [Ss]ecurity [Ss]ystem")

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
    if active_port is not None:
        active_port.addCommandFromText(line)
    else:
        print("Could not add command, since no active port is active! [", line, "]")
    # We need to look through commands to get the security systems!
    if re.match(security_system_regex, line):
        security_systems.add(SecuritySystem(line))


def createUML(ports, trace_routes):
    links_to_add = []

    result = ""
    result += "@startuml\n"
    result += "title\nProudly powered by\n <size:30><b>SeriOusBusiness_S</b>™℠®© Pat. Pend.</size>\n &\n <size:30>PandaPosse Inc.™℠®©</size>\nendtitle\n"
    result += "skinparam backgroundColor #000000\n"
    result += "skinparam databaseBorderColor #00FF00\n"
    result += "skinparam nodeBorderColor #00FF00\n"
    result += "skinparam objectBackgroundColor #000000\n"
    result += "skinparam defaultFontColor #00FF00\n"
    result += "skinparam objectBorderColor #00FF00\n"
    result += "skinparam objectFontSize 17\n"
    result += "skinparam shadowing false\n"
    result += "skinparam objectStereotypeFontSize 15\n"
    result += "skinparam objectStereotypeFontColor #00FF00\n"
    
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
            if command.visible:
                result += str(command) + "\n"

            if command.show_link:
                links_to_add.append(command)

        
        result += "}\n"

    result += "together {\n"
    for trace_route in trace_routes:
        result += "database " + trace_route.name + "{\n"
        result += "}\n"
    result += "}\n"
    result += "together {\n"
    for security_system in security_systems:
        result += "node " + security_system.name + "{\n"
        result += "}\n"
    result += "}\n"
    for link in links_to_add:

        origin = "Port_%s" % link.origin
        if isinstance(link, BruteForceCommand):
            target = "SecuritySystem_%s" % link.target
        elif isinstance(link, AddNodeToTraceRouteCommand):
            target = "Traceroute_%s" % link.target
        else:
            target = "Port_%s" % link.target
        line_char = "-"
        if link.limited:
            line_char = "."
        result += origin + " " + line_char + "[%s]" % link.color  + line_char + "|> " + target + " : <color:%s>" % link.color + link.description + "</color>\n"

    result += "footer\n"
    result += "The content of this image is confidential and intended for you only.\n " \
              "It is strictly forbidden to share any part of this image with any third party, without a written consent of SeriOusBusiness_S.\n" \
              "If you received this image by mistake, please contact SeriOusBusiness_S, together with a Dank Meme, and follow with its deletion, so that we can ensure such a mistake does not occur in the future.\n"
    result += "PandaPosse puts the security of you at a high priority. Therefore, we have put efforts into ensuring that the image is error and virus-free.\n" \
              "Unfortunately, full security of the image cannot be ensured as, despite our efforts, the data included in image could be infected, intercepted, or corrupted.\n" \
              "Therefore, the recipient should check the image for threats with proper software, as we do not accept liability for any damage inflicted by viewing the content of this image.\n"
    result += "Is it necessary to print this Image? If you care about the environment like we do, please refrain from printing. \n" \
              "It helps to keep the environment forested and litter-free. Panda's are fucking little enough as is!\n"
    result += "endfooter\n"
    result += "@enduml"
    return result


with open("result.txt", "w") as f:
    f.write(createUML(ports, trace_routes))

os.system("java -jar plantuml.jar result.txt")
