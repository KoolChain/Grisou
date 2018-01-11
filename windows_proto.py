#!/usr/bin/env python 

import asyncio
import sys
import stream


async def process_in_term():
    process = await asyncio.create_subprocess_exec(*["cmd", "/c", "start", "/wait", "cmd.exe", "/k", "TITLE custom-title & echoist_win.bat OUI"])
    print("Create called")
    return await process.wait()


if __name__ == "__main__":
    if sys.platform == 'win32':
        loop = asyncio.ProactorEventLoop()
        asyncio.set_event_loop(loop)
    else:
        raise Exception("Does not recognize a Windows platform")

    loop.run_until_complete(process_in_term())
    loop.close()

