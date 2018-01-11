#!/usr/bin/env python


from context_utils import AllContexts 

import stream

import argparse
import asyncio
import json
import platform
import subprocess
import sys


class NullSystemProcess:
    async def wait(self):
        await sleep(3600*24*365*100) #TODO replace with an infinite block on a future

    def terminate(self):
        pass


class Process:
    def __init__(self):
        self.terminate_event = asyncio.Event()

    def _platform_terminal_launch(self, title, command):
        name = platform.system()
        if name.startswith("Windows"):
            # 'start' is a builtin command of cmd shell
            return ["cmd", "/c", "start", "/wait", "cmd.exe", "/k", "TITLE {} & {}".format(title, command)]
        elif name.startswith("CYGWIN"):
            # -w to wait until started process terminates
            return ["cygstart", "-w", "cmd.exe", "/k", "\"TITLE {} & {}\"".format(title, command)]
        elif name == "Linux":
            return ["xterm", "-hold", "-e", command]
        else:
            raise Exception("Unsupported platform")

    def _platform_terminate(self):
        name = platform.system()
        if name.startswith("Windows") or name.startswith("CYGWIN"):
            # see: https://stackoverflow.com/a/42933315/1027706
            # Uses subprocess, terminate should remain a synchronous operation
            searchfilter = "WINDOWTITLE eq {}*".format(self.title) 
            # Piping stdout so it does not show up in the terminal output
            subprocess.run(["TASKKILL", "/fi", searchfilter, "/t", "/f"], stdout=subprocess.PIPE)
        elif name == "Linux":
            self.process.terminate()

    async def async_run(self, title, command):
        try:
            self.title = title
            self.command_line = self._platform_terminal_launch(title, command)
            await self._create_process()
            while True:
                done, pending = await asyncio.wait([self.process.wait(), self.terminate_event.wait()],
                                                   return_when=asyncio.FIRST_COMPLETED,
                )
                # To raise potential exception
                result = done.pop().result()

                if self.terminate_event.is_set():
                    self.terminate_event.clear()
                    return

                print("Process externally closed, relaunch it")
                await asyncio.sleep(2)
                await self._create_process()
        except Exception as e:
            print("Exception in Process::async_run(): {}".format(e))

    def terminate(self):
        self.terminate_event.set()
        self._platform_terminate()

    async def _create_process(self):
        self.process = await asyncio.create_subprocess_exec(*self.command_line)


class MiningApp:
    def __init__(self, command):
        self.command = command

    def get_command(self, **config):
        return self.command.format(**config)


#class EchoApp(MiningApp):
#    def __init__(self):
#        super().__init__("./echoist.sh {wallet}")
        

class Request():
    def __init__(self, action, workers, currency):
        self.action = action
        self.workers = workers
        self.currency = currency


class Worker:
    def __init__(self, device_id):
        self.device_id = device_id
        self.command_queue = asyncio.Queue()
        self.process = None
        self.last_mine_request = None
        asyncio.ensure_future(self._async_mine())
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._stop()
        return False

    def mine(self, mining_app, currency_config):
        self.last_mine_request = (mining_app, currency_config)
        self.command_queue.put_nowait(self.last_mine_request)

    def pause(self):
        self._stop()

    def resume(self):
        if self.last_mine_request:
            self.command_queue.put_nowait(self.last_mine_request)
        else:
            print("Cannot resume a worker that never ran.")

    def _stop(self):
        if self.process:
            self.process.terminate()
            self.process = None

    async def _async_mine(self):
        while True:
            mining_app, currency_config = await self.command_queue.get()

            if self.process:
                self.process.terminate()
                # Await until the currently executing process.async_run completes
                # (not required, since the soon-to-be replaced self.process is captured in asyncio)
                await self.process_future
            else:
                self.process = Process()

            self.process_future = asyncio.ensure_future(
                self.process.async_run("Grisou worker on device #{}".format(self.device_id),
                                        mining_app.get_command(device_id = self.device_id,
                                                              **currency_config)))


class CommandPrompt:
    def __init__(self, workers):
        self.workers = workers

    def _get_workers(self, read):
        ids = read.split()[1:]
        if not ids:
            return self.workers
        else:
            result = []
            try:
                result = [self.workers[int(i)] for i in ids]
            except ValueError:
                print("Worker index must be an integer, ignoring request")
            except IndexError:
                print("Worker index out of range, ignoring request")
            return result

    def _get_verb(self, read):
        return read.split()[0]

    def _get_currency(self, read):
        return read.split()[0].upper()

    async def interact(self):
        read = await stream.ainput(prompt="Request: ")
        verb = self._get_verb(read)
        if verb == "pause" or verb == "resume":
            return Request(verb, self._get_workers(read), None)
        else:
            return Request("mine", self._get_workers(read), self._get_currency(read))


async def async_interact_loop(prompt, currency_to_app, currency_to_config):
    while True:
        request = await prompt.interact()
        try:
            if request.action == "pause":
                func = lambda worker: worker.pause()
            elif request.action == "resume":
                func = lambda worker: worker.resume()
            else:
                func = lambda worker: worker.mine(currency_to_app[request.currency],
                                                  currency_to_config[request.currency])

            for worker in request.workers:
                func(worker)

        except KeyError as e:
            print("Currency {} not available.".format(request.currency))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Control mining processes')
    parser.add_argument('worker_count', metavar='N', type=int, 
                        help='Number of workers to start')
    parser.add_argument('--config', default="currencies.json",
                        help='The currencies config file')
    parser.add_argument('--applications', default="applications.json",
                        help='The applications config file')
    parser.add_argument('--debug', action="store_true",
                        help='Debug mode notably enables the event loop debug mode')
    args = parser.parse_args()

    # Must be done before any use of the loop (notably ensure_future)
    if sys.platform == 'win32':
        if (args.debug):
            print("[DEBUG] Detected Win32, installs proactor event loop.")
        asyncio.set_event_loop(asyncio.ProactorEventLoop())

    mining_configs = json.load(open(args.config))

    apps = json.load(open(args.applications))
    mining_apps = {key: MiningApp(path) for (key, path) in apps.items()}

    workers = [Worker(i) for i in range(args.worker_count)]

    prompt = CommandPrompt(workers)

    loop = asyncio.get_event_loop()
    loop.set_debug(args.debug)

    with AllContexts(*workers):
        top_async = async_interact_loop(prompt, mining_apps, mining_configs) 
        rc = loop.run_until_complete(top_async)

    loop.close()

