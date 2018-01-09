#!/usr/bin/env python

import stream

import argparse
import asyncio
import json


class NullSystemProcess:
    async def wait(self):
        await sleep(3600*24*365*10) #TODO replace with an infinit block on a future

    def terminate(self):
        pass


class Process:
    def __init__(self):
        self.terminate_event = asyncio.Event()

    async def async_run(self, command):
        self.command_line = ["xterm", "-e", command]
        await self._create_process()
        while True:
            done, pending = await asyncio.wait([self.process.wait(), self.terminate_event.wait()],
                                               return_when=asyncio.FIRST_COMPLETED,
            )
            # To raise potential exception
            result = done.pop().result();

            if self.terminate_event.is_set():
                return

            print("Process externally closed, relaunch it")
            await self._create_process()

    #async def async_start(self):
    #    self.process = NullSystemProcess();
    #    while True:
    #        wait_list = [self.command_queue.get(), process.wait()]
    #        done, pending = await asyncio.wait(wait_list,
    #                                           return_when=asyncio.FIRST_COMPLETED,
    #        )
    #        result = done.pop().result();
    #        if type(result) is Request:
    #            process.terminate();
    #            self.command_line = ["xterm", "-e", result.value]
    #        else:
    #            print("Process externally closed, relaunch it")
    #        await _create_process()
    #
    #def set_command(self, command):
    #    self.command_queue = Request(command)

    def terminate(self):
        self.terminate_event.set()
        self.process.terminate()

    async def _create_process(self):
        self.process = await asyncio.create_subprocess_exec(*self.command_line)


class MiningApp:
    def __init__(self, command):
        self.command = command

    def get_command(self, **config):
        return self.command.format(**config)


class Request():
    def __init__(self, value):
        self.value = value


class Worker:
    def __init__(self, device_id):
        self.device_id = device_id
        self.command_queue = asyncio.Queue()
    
    def set_request(self, request):
        self.command_queue.put_nowait(Request(request))

    async def mine(self, mining_app, currency_config):
        self.process = Process()
        wait_list = [
            self.process.async_run(mining_app.get_command(device_id = self.device_id, **currency_config)),
            self.command_queue.get(),
        ]
        done, pending = await asyncio.wait(wait_list, return_when=asyncio.FIRST_COMPLETED)

        result = done.pop().result();
        if type(result) is Request:
            self.process.terminate();
        
    
class CommandPrompt:
    def __init__(self, workers):
        self.workers = workers

    def _get_workers(self, request):
        # TODO
        return [self.workers[0]]

    def _get_worker_command(self, read):
        # TODO
        return read

    async def interact(self):
        while True:
            read = await stream.ainput(prompt="Request: ")
            for worker in self._get_workers(read):
                worker.set_request(self._get_worker_command(read))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Control mining processes')
    parser.add_argument('worker_count', metavar='N', type=int, 
                        help='Number of workers to start')
    parser.add_argument('--config', default="currencies.json",
                        help='The currencies config file')
    args = parser.parse_args()

    #currencies = json.load(open(args.config))
    #workers = [Worker(i, ) for i in

    mining_apps = {
        "XMR": MiningApp("./echoist.sh {pool}"),
        "HUSH": MiningApp("./echoist.sh {wallet}"),
    }

    wk = Worker(0)
    asyncio.ensure_future(wk.mine(mining_apps["XMR"], {"pool": "lepool", "wallet":"lewallet"}))

    prompt = CommandPrompt([wk])
    asyncio.ensure_future(prompt.interact())
    
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    rc = loop.run_forever()
    loop.close()
    
