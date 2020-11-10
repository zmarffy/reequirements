import subprocess
import warnings

ERROR_MSG = "Requirement {} not fulfilled or configured correctly; command {} returned a non-zero exit code, {}, with output:\n\n{}"


class RequirementMissing(Exception):

    def __init__(self, requirement, output, exit_code):
        self.requirement = requirement
        self.output = output
        self.exit_code = exit_code
        super().__init__(ERROR_MSG.format(self.requirement.name,
                                          self.requirement.command, exit_code, output))


class Requirement():

    def __init__(self, name, command, warning=False):
        self.name = name
        self.command = command
        self.warning = warning

    def check(self):
        try:
            subprocess.check_output(self.command, stderr=subprocess.STDOUT)
            return True
        except subprocess.CalledProcessError as e:
            output = e.output.decode().strip()
            if not self.warning:
                raise RequirementMissing(self, output, e.returncode) from None
            else:
                warnings.warn(ERROR_MSG.format(
                    self.name, self.command, e.returncode, output), RequirementWarning, stacklevel=2)
                return False


class RequirementWarning(Warning):
    """A warning for when certain requirements are missing"""
