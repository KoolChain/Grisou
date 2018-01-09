#!/usr/bin/env python 

import asyncio
import sys
import stream


async def process_in_term(queue, loop):
    process = await asyncio.create_subprocess_exec(*["xterm", "-e", "./echoist.sh", "oui"])

    while True:
        done, pending = await asyncio.wait( [
                process.wait(), 
                queue.get(),
            ],
            return_when=asyncio.FIRST_COMPLETED,
            loop = loop,
        )
        result = done.pop().result();
        if type(result) is Command:
            process.terminate();
            process = await asyncio.create_subprocess_exec(*["xterm", "-e", "./echoist.sh", result.value])
        else:
            print("Process externally closed")
            return;


class Command():
    def __init__(self, value):
        self.value = value


async def interact(queue, loop):
    while True:
        read = await stream.ainput(prompt="Script: ", loop=loop),
        queue.put_nowait(Command(read[0]))


async def wait_approach(loop):
    done, pending = await asyncio.wait([
            process_in_term(queue, loop),
            interact(queue, loop),
        ],
        return_when=asyncio.FIRST_EXCEPTION,
    )

    for fut in done:
        if fut.exception():
            fut.result()


def schedule_approach(loop):
    asyncio.ensure_future(process_in_term(queue, loop))
    asyncio.ensure_future(interact(queue, loop))
    rc = loop.run_forever()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    queue = asyncio.Queue(loop=loop)

    rc = loop.run_until_complete(wait_approach(loop))

    #schedule_approach(loop)

    loop.close()

