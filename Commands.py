import re


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

        self.show_link = False

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
        self.show_link = True

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
        self._target_regex = re.compile("^(\-|>)?\s*Link( up|) . QPU to [pP]ort (\d+)")
        self._amount_regex = re.compile("^(\-|>)?\s*Link( up|) (\d+)")
        self._prefix = "~"
        self.color = "#0000ff"
        self.show_link = True

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
        self._target_regex = re.compile("^(\-|>)?\s*Brute [fF]orce [sS]ecurity [sS]ystem (\d+)")
        self._amount_regex = re.compile("(?=((\d+) damage{1}))")
        self._prefix = "-"
        self.color = "#ff0000"
        self.show_link = True

    @property
    def description(self):
        return "Attack (%s dmg)" % self.amount


class AddNodeToTraceRouteCommand(Command):
    def __init__(self, name):
        super().__init__(name)
        self._target_regex = re.compile("^(\-|>)?\s*Add . nodes to [Tt]race [Rr]oute (\d+)")

        self._amount_regex = re.compile("^(\-|>)?\s*Add (\d+) ")
        self._prefix = "~"
        self.color = "#0000ff"

        self.show_link = True

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
        self._target_regex = re.compile("^(\-|>)?\s*((Divert)|(Redirect up to)) . QPU from [pP]ort . to [Pp]ort (\d+)")
        self._amount_regex = re.compile("^(\-|>)?\s*((Divert)|(Redirect up to)) (\d+|#)")
        self._from_regex = re.compile("^(\-|>)?\s*((Divert)|(Redirect up to)) . QPU from [pP]ort (\d+)")

        self._prefix = "~"
        self.color = "#0000ff"
        self.show_link = True

    @property
    def description(self):
        if str(self.origin) != str(self.fro):
            return "Redirect %s QPU (from Port_%s)" % (self.amount, self.fro)
        return "Redirect %s QPU" % self.amount


class CommandFactory:

    @classmethod
    def createCommandFromText(cls, text):
        link_qpu_regex = re.compile("^(\-|>)?\s*Link( up|) . QPU to [pP]ort")
        brute_force_regex = re.compile('^(\-|>)?\s*Brute [Ff]orce [Ss]ecurity [Ss]ystem .')
        add_node_to_trace_route_regext = re.compile('^(\-|>)?\s*Add . nodes to [Tt]race [Rr]oute .')
        connect_to_port_regex = re.compile("^(\-|>)?\s*Connect to port")
        initial_connect_regex = re.compile("^(\-|>)?\s*Initial connect")
        redirect_qpu_regex = re.compile("^(\-|>)?\s*Redirect up to . QPU from [pP]ort .|(\-|>)?\s* Divert . QPU from [pP]ort")
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