import re
import os


class Command:
    def __init__(self, name):
        self._name = name
        self._target_regex = None
        self._amount_regex = None
        self._from_regex = None
        self._target = None
        self._amount = None
        self._origin = None
        self._prefix = None
        self.visible = True  # Some commands (such as brute force one) can have multiple targets. We split these up
        self._port = None
        self._from = None
        self.color = "#FFFFFF"
        self._description = "No idea!"

        self._limited = False

    @property
    def limited(self):
        return self._limited

    def setPort(self, port):
        self._port = port

    @property
    def description(self):
        return self._description

    def __repr__(self):
        return "<COMMAND> " + self.name

    def __str__(self):
        return self.name

    @property
    def name(self):
        result = re.sub(r'^(\-|>)\s', "", self._name)
        if self._prefix is not None:
            return self._prefix + " " + result
        return result

    @property
    def target(self):
        if self._target is None and self._target_regex is not None:
            m = self._target_regex.search(self._name)
            self._target = m.groups()[-1]

        return self._target

    @property
    def amount(self):
        if self._amount is None and self._amount_regex is not None:
            m = self._amount_regex.search(self._name)
            self._amount = m.groups()[-1]

        return self._amount

    @property
    def fro(self):
        if self._from is None and self._from_regex is not None:
            m = self._from_regex.search(self._name)
            self._from = m.groups()[-1]
        return self._from

    @property
    def origin(self):
        if self._origin is None and self._port is not None:
            return self._port.index
        return self._origin


class ConnectionCommand(Command):
    def __init__(self, name):
        super().__init__(name)
        self._target_regex = re.compile("^(\-|>)?\s*Connect to port (\d+)")
        self._prefix = "+"
        self.color = "#00FF00"
        self._description = "Connect"

        if "<can only connect" in name:
            self._limited = True


class InitialConnectCommand(Command):
    pass


class LinkQPUCommand(Command):
    def __init__(self, name):
        """
        Examples of this command:
        > Link up 1 QPU to port 1
        > Link 5 QPU to port 3 (Maximum of 3 times per hack)
        - Link 2 QPU to port 7
        :param name:
        """
        super().__init__(name)
        self._target_regex = re.compile("^(\-|>)?\s*Link( up|) . QPU to port (\d+)")
        self._amount_regex = re.compile("^(\-|>)?\s*Link( up|) (\d+)")
        self._prefix = "~"
        self.color = "#0000ff"

        if "Maximum of" in self._name:
            self._limited = True

    @property
    def description(self):
        return "Link %s QPU" % self.amount


class BruteForceCommand(Command):
    def __init__(self, name):
        """
        - Brute force Security System 3, 2 damage
        - Brute force security system 3, 5 damage
        > Brute force security system 1, 2 and 3, 1 damage, costs 1 QPU linked to port 3
        :param name:
        """
        super().__init__(name)
        self._target_regex = re.compile("^(\-|>)?\s*Brute force [sS]ecurity [sS]ystem (\d+)")
        self._amount_regex = re.compile("(?=((\d+) damage{1}))")
        self._prefix = "-"
        self.color = "#ff0000"

    @property
    def description(self):
        return "Attack (%s dmg)" % self.amount


class AddNodeToTraceRouteCommand(Command):
    def __init__(self, name):
        super().__init__(name)
        self._target_regex = re.compile("^(\-|>)?\s*Add . nodes to Trace Route (\d+)")

        self._amount_regex = re.compile("^(\-|>)?\s*Add (\d+) ")
        self._prefix = "~"
        self.color = "#0000ff"

    @property
    def description(self):
        return "Add %s nodes" % self.amount


class RedirectQPUCommand(Command):
    def __init__(self, name):
        """
        - Redirect up to 3 QPU from port 3 to port 5
        > Direct 2 QPU from port 3 to port 1
        :param name:
        """
        super().__init__(name)
        self._target_regex = re.compile("^(\-|>)?\s*((Divert)|(Redirect up to)) . QPU from port . to port (\d+)")
        self._amount_regex = re.compile("^(\-|>)?\s*((Divert)|(Redirect up to)) (\d+|#)")
        self._from_regex = re.compile("^(\-|>)?\s*((Divert)|(Redirect up to)) . QPU from port (\d+)")

        self._prefix = "~"
        self.color = "#0000ff"

    @property
    def description(self):
        if self.origin != self.fro:
            return "Redirect %s QPU (from Port_%s)" % (self.amount, self.fro)
        return "Redirect %s QPU" % self.amount


class CommandFactory:

    @classmethod
    def createCommandFromText(cls, text):
        link_qpu_regex = re.compile("^(\-|>)?\s*Link( up|) . QPU to port")
        brute_force_regex = re.compile('^(\-|>)?\s*Brute force [Ss]ecurity [Ss]ystem .')
        add_node_to_trace_route_regext = re.compile('^(\-|>)?\s*Add . nodes to Trace Route .')
        connect_to_port_regex = re.compile("^(\-|>)?\s*Connect to port")
        initial_connect_regex = re.compile("^(\-|>)?\s*Initial connect")
        redirect_qpu_regex = re.compile("^(\-|>)?\s*Redirect up to . QPU from port .|(\-|>)?\s* Divert . QPU from port")
        if re.match(connect_to_port_regex, text):
            return ConnectionCommand(text)
        elif re.match(initial_connect_regex, text):
            return InitialConnectCommand(text)
        elif re.match(link_qpu_regex, text):
            return LinkQPUCommand(text)
        elif re.match(brute_force_regex, text):
            # Check if multiple brute force commands are needed.
            reg = re.compile("(^.*(?=(\d damage)))")
            is_single_targets_regex = re.compile("^(\-|>)?\s*Brute force [sS]ecurity [sS]ystem \d, \d damage")
            single_target = is_single_targets_regex.search(text)
            if single_target:
                return BruteForceCommand(text)

            pruned_text = reg.search(text).group(1)
            all_targets_regex = re.compile("(\d,(\d)|\d and(\d)|\d)")
            all_targets = re.findall(all_targets_regex, pruned_text)
            results = []
            results.append(BruteForceCommand(text))
            for target in all_targets[1:]:
                command = BruteForceCommand(text)
                command.visible = False
                command._target = target[0]
                results.append(command)
            return results
        elif re.match(add_node_to_trace_route_regext, text):
            return AddNodeToTraceRouteCommand(text)
        elif re.match(redirect_qpu_regex, text):
            return RedirectQPUCommand(text)
        return Command(text)    


class TraceRoute:
    def __init__(self, line):
        self._line = line
        self._system_number_regex = re.compile("Nodes in trace route (\d+) at the start|Trace Route (\d+)")
        match = re.match(self._system_number_regex, line)
        if match.group(1) is not None:
            tracesystem_number = match.group(1)
        else:
            tracesystem_number = match.group(2)
        self._name = "Traceroute_%s" % tracesystem_number

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
        self._system_number_regex = re.compile("^(\-|>)?\s*Brute force [sS]ecurity [sS]ystem (\d+)")
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
trace_route_regex = re.compile("Nodes in trace route . at the start|Trace Route .")
security_system_regex = re.compile("^(\-|>)?\s*Brute force [Ss]ecurity [Ss]ystem")

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

            if isinstance(command, ConnectionCommand):
                links_to_add.append(command)
            elif isinstance(command, AddNodeToTraceRouteCommand):
                links_to_add.append(command)
            elif isinstance(command, LinkQPUCommand):
                links_to_add.append(command)
            elif isinstance(command, RedirectQPUCommand):
                links_to_add.append(command)
            elif isinstance(command, BruteForceCommand):
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
