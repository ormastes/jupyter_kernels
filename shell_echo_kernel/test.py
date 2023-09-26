import asyncio
import subprocess
import os


class Shell:
    @staticmethod
    def length(s):
        n = len(s)
        if os.name == 'nt':
            return n + s.count('\n')
        else:
            return n

    async def _run(self):
        f = open("output.txt", "w")
        self.proc = await asyncio.create_subprocess_exec(
            'clang-repl.exe',
            stdout=f, #asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE, stdin=subprocess.PIPE)

        outs = bytearray()
        count = self.length('clang-repl> ')

        #stdoutdata = await self.proc.stdout.read(count)
        #outs += stdoutdata

    async def _do_execute(self):
        self.proc.stdin.write('#include<cstdio>\nprintf("hello, world");fflush(stdout);\n'.encode('utf-8'))
        await self.proc.stdin.drain()
        self.proc.stdin.write('fflush(stdout);\n'.encode('utf-8'))
        await self.proc.stdin.drain()
        outs = bytearray()
        count = self.length('#include<cstdio>\nprintf("hello, world");fflush(stdout);\n' + 'clang-repl> ')
        #stdoutdata = await self.proc.stdout.read(count)
        #outs += stdoutdata
        #print('outs: ', outs.decode('utf-8'))

        #self.proc.stdin.close()
        #await self.proc.wait()

shell = Shell()

def outputs():
    with open("output.txt", "r") as f:
        while True:
            c = f.read()
            print(c)
            # sleep 1 sec
            import time
            time.sleep(1)

try:
    loop = asyncio.get_event_loop()
except RuntimeError as e:
    if str(e).startswith('There is no current event loop in thread'):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        pass
    else:
        raise e
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(shell._run())
    import threading
    x = threading.Thread(target=outputs)
    x.start()
    loop.run_until_complete(shell._do_execute())
finally:
    x.join()
    loop.close()
    asyncio.set_event_loop(None)
