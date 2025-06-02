import asyncio
import threading
import time

class RemoteDict:
    def __init__(self, address="127.0.0.1", port=6379):
        self._data = {}
        self._address = address
        self._port = port
        self._server = None
        self._server_task = None

    async def start(self):
        self._server = await asyncio.start_server(self._handle_request, self._address, self._port)
        self._server_task = asyncio.create_task(self._server.serve_forever())
        print(f"Server started on {self._address}:{self._port}")

    async def stop(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            if self._server_task:
                self._server_task.cancel()
            print("Server stopped.")

    async def _handle_request(self, reader, writer):
        try:
            while True:
                # Read the first line (RESP type)
                line = await reader.readline()
                if not line:
                    break
                if line.startswith(b'*'):  # Array (command)
                    num_args = int(line[1:].strip())
                    args = []
                    for _ in range(num_args):
                        length_line = await reader.readline()
                        if not length_line.startswith(b'$'):
                            writer.write(b'-ERR Protocol error\r\n')
                            await writer.drain()
                            return
                        length = int(length_line[1:].strip())
                        arg = await reader.readexactly(length)
                        await reader.readexactly(2)  # Discard \r\n
                        args.append(arg.decode())
                    if not args:
                        writer.write(b'-ERR Empty command\r\n')
                        await writer.drain()
                        continue
                    cmd = args[0].upper()
                    response = None
                    if cmd == 'SET' and len(args) == 3:
                        self._set(args[1], args[2])
                        writer.write(b'+OK\r\n')
                    elif cmd == 'GET' and len(args) == 2:
                        response = self._get(args[1])
                        if response is not None:
                            writer.write(response)
                        else:
                            writer.write(b'$-1\r\n')
                    elif cmd == 'DEL' and len(args) >= 2:
                        count = self._del(args[1:])
                        writer.write(f":{count}\r\n".encode())
                    elif cmd == 'EXISTS' and len(args) >= 2:
                        count = self._exists(args[1:])
                        writer.write(f":{count}\r\n".encode())
                    elif cmd == 'KEYS' and len(args) == 2:
                        keys = self._keys(args[1])
                        resp = f"*{len(keys)}\r\n"
                        for k in keys:
                            resp += f"${len(k)}\r\n{k}\r\n"
                        writer.write(resp.encode())
                    elif cmd == 'FLUSHDB' and len(args) == 1:
                        self._flushdb()
                        writer.write(b'+OK\r\n')
                    elif cmd == 'FLUSHALL' and len(args) == 1:
                        self._flushall()
                        writer.write(b'+OK\r\n')
                    else:
                        writer.write(b'-ERR unknown command or wrong number of arguments\r\n')
                        await writer.drain()
                        continue
                    await writer.drain()
                else:
                    writer.write(b'-ERR Protocol error: expected array\r\n')
                    await writer.drain()
                    break
        except Exception as e:
            writer.write(f'-ERR {e}\r\n'.encode())
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    def _set(self, key, value):
        self._data[key] = value

    def _get(self, key):
        value = self._data.get(key)
        if value is not None:
            resp = f"${len(value)}\r\n{value}\r\n"
            return resp.encode()
        else:
            return None

    def _del(self, keys):
        count = 0
        for key in keys:
            if key in self._data:
                del self._data[key]
                count += 1
        return count

    def _exists(self, keys):
        count = 0
        for key in keys:
            if key in self._data:
                count += 1
        return count

    def _keys(self, pattern):
        import fnmatch
        return [k for k in self._data.keys() if fnmatch.fnmatch(k, pattern)]

    def _flushdb(self):
        self._data.clear()

    def _flushall(self):
        self._data.clear()

    def start_thread(self):
        def run():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self.start())
            try:
                self._loop.run_forever()
            finally:
                self._loop.close()
        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()
        time.sleep(0.5)  # Give the server a moment to start

    def stop_thread(self):
        """Stop the server safely from the main thread."""
        if hasattr(self, '_loop') and self._loop.is_running():
            fut = asyncio.run_coroutine_threadsafe(self.stop(), self._loop)
            fut.result()  # Wait for stop to complete