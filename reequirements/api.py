import subprocess
import warnings

BASE_ERROR_MSG = "Requirement {} error; command {} returned a non-zero exit code, {}, with output:\n\n{}"
MISSING_ERROR_MSG = "Requirement {} not fulfilled; command {} not found"


class RequirementError(Exception):

    def __init__(self, requirement, output, exit_code):
        self.requirement = requirement
        self.output = output
        self.exit_code = exit_code
        super().__init__(self._generate_message())

    def _generate_message(self):
        return BASE_ERROR_MSG.format(self.requirement.name, self.requirement.command, self.exit_code, self.output)


class RequirementMissing(RequirementError):

    def __init__(self, requirement):
        self.requirement = requirement
        self.output = ""
        self.exit_code = 127
        super().__init__(self.requirement, self.output, self.exit_code)

    def _generate_message(self):
        return MISSING_ERROR_MSG.format(self.requirement.name, self.requirement.command)


class Requirement():

    def __init__(self, name, command, warn=False):
        self.name = name
        self.command = command
        self.warn = warn

    def check(self):
        try:
            subprocess.check_output(self.command, stderr=subprocess.STDOUT)
            return True
        except FileNotFoundError:
            if not self.warn:
                raise RequirementMissing(self) from None
            else:
                warnings.warn(MISSING_ERROR_MSG.format(
                    self.name, self.command), RequirementMissingWarning, stacklevel=2)
                return False
        except subprocess.CalledProcessError as e:
            output = e.output.decode().strip()
            if not self.warn:
                raise RequirementError(self, output, e.returncode) from None
            else:
                warnings.warn(BASE_ERROR_MSG.format(
                    self.name, self.command, e.returncode, output), RequirementWarning, stacklevel=2)
            return False


class RequirementWarning(Warning):
    """A warning for when certain requirements are not met for one reason or another"""


class RequirementMissingWarning(RequirementWarning):
    """A warning for when certain requirements are missing"""
