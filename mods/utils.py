import json
import os
import sys
import time

import psutil
from termcolor import cprint


class utils:
    @staticmethod
    def tryWait(
        function_name,
        argz: list,
        timeout: int,
        desc: str = None,
        verbose=True,
    ):
        """[summary]

        Args:
            function_name (function): The function object which needed to be tried
            argz (list): The arguments that must be passed to the function
            timeout (int): Maximum timeout in seconds
            desc (str): Description that needed to be printed inside the verbose line
            verbose (bool, optional): Boolean value which turns the verbose mode on. Defaults to True.

        Returns:
            object: Any object returned by the function
        """
        for _ in range(timeout):
            try:
                return_objs = function_name(*argz)
                if return_objs:
                    return return_objs
                else:
                    time.sleep(1)
            except:
                time.sleep(1)
        if verbose:
            cprint(f"❗ Function execution failed for '{desc}' @ {function_name}", "red")

    # Tries for given time and returns the return_object on success
    @staticmethod
    def tryExcept(function_name, argz: list, timeout: int, desc=None, verbose=True):
        """Tries for given time and returns tries_left on success"""
        for i in range(timeout):
            try:
                function_name(*argz)
                return timeout - i - 1
            except:
                time.sleep(1)
        if verbose:
            cprint(f"❗ Function execution failed for '{desc}' @ {function_name}", "red")

    @staticmethod
    def replace_chars(name: str, keywords: str, to: str):
        for i in keywords:
            name = name.replace(i, to)
        return name

    @staticmethod
    def makedir(path: str, verbose=False):
        """Creates a directory only if does not exist and not throw any error if it exists

        Args:
            path (str): Path inclusive of directory name
            verbose (bool, optional): Turns on the verbose mode. Defaults to False.
        """
        if not os.path.exists(path):
            os.mkdir(path)
            if verbose:
                cprint(f"\t✅  Directory created : '{path}'", "green")
        elif verbose:
            cprint(f"\t❎  Directory existed : '{path}'", "cyan")

    @staticmethod
    def killproc(name: str):
        cprint(f"[i] Killing all the {name} instances", "cyan")
        print()
        count = 0
        for p in psutil.process_iter():
            try:
                if p.name() == name:
                    count += 1
                    utils.clearPrint()
                    cprint(f" |-> ", "white", attrs=["blink"], end="")
                    cprint(f"Killed [", "green", end="")
                    cprint(f"{count}", "yellow", end="")
                    cprint(f"] instances of {p.name()} ", "green")
                    p.kill()
            except (psutil.AccessDenied, psutil.ZombieProcess):
                cprint(f"\n |-> Access Denied while killing {p.name()}", "red")
                continue
            except psutil.NoSuchProcess:
                continue
        if count == 0:
            utils.clearPrint()
            cprint(f" |-> ", "white", attrs=["blink"], end="")
            cprint(f"There was none.", "cyan", end="")
            cprint(f" FUNCTION_ABORT!", "red", end="\n")

    @staticmethod
    def clearPrint():
        CURSOR_UP_ONE = "\x1b[1A"
        ERASE_LINE = "\x1b[2K"
        sys.stdout.write(CURSOR_UP_ONE)
        sys.stdout.write(ERASE_LINE)

    @staticmethod
    def jsonLoad(path: str):
        try:
            with open(path, "r") as f:
                JSON = json.load(f)
                cprint(f" |> ", "cyan", attrs=["blink"], end="")
                cprint(f"[i] Retriving {len(JSON)} links from ", "cyan", end="")
                cprint(f"{path}", "magenta")
        except:
            JSON = {}
        return JSON

    @staticmethod
    def updateUltimatum(ultimatum: dict, sub_name: str):
        _dir = os.getcwd() + "\\media\\" + sub_name
        path = _dir + f"\\{sub_name}.json"
        if os.path.exists(path):
            ultimatum.update(utils.jsonLoad(path))
