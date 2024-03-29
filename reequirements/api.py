import subprocess
import warnings

BASE_ERROR_MSG = "Requirement {} error; command {} returned a non-zero exit code, {}, with output:\n\n{}"
MISSING_ERROR_MSG = "Requirement {} not fulfilled; command {} not found"

# Variables utilized as a "cache" so duplicate requirement-checking does not happen and waste time and CPU cycles
REQUIREMENTS_FULFILLED = []
REQUIREMENTS_UNFULFILLED = []


class RequirementError(Exception):

    """An exception to throw when a requirement does not pass the requirement check test.

    Args:
        requirement (Requirement): The Requirement object that did not pass the requirement check test.
        output (str): The text output of the command that did not pass the requirement check test.
        exit_code (int): The code that the requirement command exited with.

    Attributes:
        requirement (Requirement): The Requirement object that did not pass the requirement check test.
        output (str): The text output of the command that did not pass the requirement check test.
        exit_code (int): The code that the requirement command exited with.
        msg (str): Human readable string describing the exception.
    """

    def __init__(self, requirement: "Requirement", output: str, exit_code: int) -> None:
        self.requirement = requirement
        self.output = output
        self.exit_code = exit_code
        super().__init__(self.msg)

    @property
    def msg(self) -> str:
        return BASE_ERROR_MSG.format(
            self.requirement.name, self.requirement.command, self.exit_code, self.output
        )


class RequirementMissing(RequirementError):

    """An exception to throw when a requirement is missing.

    Args:
        requirement (Requirement): The Requirement object that is missing.
        output (str): The text output of the command that failed.
        exit_code (int): The code that the requirement command exited with.

    Attributes:
        requirement (Requirement): The Requirement object that is missing.
        output (str): The text output of the command that failed.
        exit_code (int): The code that the requirement command exited with.
        msg (str): Human readable string describing the exception.
    """

    def __init__(self, requirement: "Requirement") -> None:
        self.requirement = requirement
        self.output = ""
        self.exit_code = 127
        super().__init__(self.requirement, self.output, self.exit_code)

    @property
    def msg(self) -> str:
        return MISSING_ERROR_MSG.format(self.requirement.name, self.requirement.command)


class Requirement:

    """Represents a requirement for a project.

    Args:
        name (str): The friendly name of the requirement.
        command (list[str]): The command to run to check the requirement.
        warn (bool, optional): If True, issue a warning instead of throwing an exception on a requirement check failure. Defaults to False.
    """

    def __init__(self, name: str, command: list[str], warn: bool = False) -> None:
        self.name = name
        self.command = command
        self.warn = warn

    def check(self) -> bool:
        """Check if a requirement is fulfilled.

        Raises:
            RequirementMissing: If the requirement is missing (command to check not found) and self.warn is False.
            RequirementError: If the requirement check fails (command to check returns any other nonzero exit code besides 127) and self.warn is False.

        Returns:
            bool: True if the requirement check passes. False if it fails and self.warn is True.
        """
        if self in REQUIREMENTS_FULFILLED:
            return True
        elif self in REQUIREMENTS_UNFULFILLED:
            return False

        try:
            subprocess.check_output(self.command, stderr=subprocess.STDOUT)
            REQUIREMENTS_FULFILLED.append(self)
            return True
        except FileNotFoundError:
            if not self.warn:
                raise RequirementMissing(self) from None
            else:
                warnings.warn(
                    MISSING_ERROR_MSG.format(self.name, self.command),
                    RequirementMissingWarning,
                    stacklevel=2,
                )
                REQUIREMENTS_UNFULFILLED.append(self)
                return False
        except subprocess.CalledProcessError as e:
            output = e.output.decode().strip()
            if not self.warn:
                raise RequirementError(self, output, e.returncode) from None
            else:
                warnings.warn(
                    BASE_ERROR_MSG.format(
                        self.name, self.command, e.returncode, output
                    ),
                    RequirementWarning,
                    stacklevel=2,
                )
            REQUIREMENTS_UNFULFILLED.append(self)
            return False

    def __eq__(self, other) -> bool:
        # Define the equality operator as "the commands are the same". This is used in checking the "checked requirements cache" so that the same requirement is not checked multiple times, which would be useless
        return self.command == other.command


class RequirementWarning(Warning):
    """A warning for when certain requirements are not met for one reason or another"""


class RequirementMissingWarning(RequirementWarning):
    """A warning for when certain requirements are missing"""
