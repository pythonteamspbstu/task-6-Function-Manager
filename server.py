import asyncio
import json
import traceback
from contextlib import asynccontextmanager
from typing import List, Dict, Any

from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
import uvicorn

from function_manager import FunctionManager
from utils import parse_csv_list

class FunctionCreate(BaseModel):
    name: str
    inputs: List[str]
    outputs: List[str]
    expression: str

class FunctionExecute(BaseModel):
    args: Dict[str, float]

manager = FunctionManager()

async def handle_tcp_client(reader, writer):
    addr = writer.get_extra_info('peername')
    print(f"New TCP connection from {addr}")

    async def send_msg(msg):
        writer.write(f"{msg}\n".encode())
        await writer.drain()

    async def read_msg(prompt=""):
        if prompt:
            writer.write(f"{prompt}".encode())
            await writer.drain()
        data = await reader.readline()
        if not data:
            # Empty read means the peer closed the connection (EOF).
            raise ConnectionResetError(f"Client {addr} disconnected")
        return data.decode().strip()

    try:
        while True:
            menu = (
                "\n--- Function Server Menu ---\n"
                "1. Create Function\n"
                "2. List Functions\n"
                "3. Get Function Details\n"
                "4. Update Function\n"
                "5. Delete Function\n"
                "6. Execute Function\n"
                "7. Exit\n"
                "Select option: "
            )
            choice = await read_msg(menu)
            
            if not choice:
                continue

            if choice == '1':
                name = await read_msg("Enter function name: ")
                inputs_str = await read_msg("Enter inputs (comma separated, e.g. x,y): ")
                inputs = parse_csv_list(inputs_str, default=[])
                outputs_str = await read_msg("Enter outputs (comma separated): ")
                outputs = parse_csv_list(outputs_str, default=[])
                expression = await read_msg("Enter expression (e.g. x + y): ")
                
                try:
                    manager.create_function(name, inputs, outputs, expression)
                    await send_msg(f"Function '{name}' created successfully.")
                except ValueError as e:
                    await send_msg(f"Error: {e}")

            elif choice == '2':
                funcs = manager.list_functions()
                if not funcs:
                    await send_msg("No functions available.")
                else:
                    await send_msg("Functions:")
                    for f in funcs:
                        await send_msg(f" - {f['name']} = {f['expression']}")

            elif choice == '3':
                name = await read_msg("Enter function name: ")
                func = manager.get_function(name)
                if func:
                    await send_msg(json.dumps(func, indent=2))
                else:
                    await send_msg("Function not found.")

            elif choice == '4':
                name = await read_msg("Enter function name to update: ")
                func = manager.get_function(name)
                if not func:
                    await send_msg("Function not found.")
                else:
                    inputs_str = await read_msg(f"Enter new inputs [{','.join(func['inputs'])}]: ")
                    inputs = parse_csv_list(inputs_str, default=func['inputs'])
                    
                    outputs_str = await read_msg(f"Enter new outputs [{','.join(func['outputs'])}]: ")
                    outputs = parse_csv_list(outputs_str, default=func['outputs'])
                    
                    expression = await read_msg(f"Enter new expression [{func['expression']}]: ")
                    if not expression: expression = func['expression']

                    try:
                        manager.update_function(name, inputs, outputs, expression)
                        await send_msg("Function updated.")
                    except ValueError as e:
                        await send_msg(f"Error: {e}")

            elif choice == '5':
                name = await read_msg("Enter function name to delete: ")
                if manager.delete_function(name):
                    await send_msg("Function deleted.")
                else:
                    await send_msg("Function not found.")

            elif choice == '6':
                name = await read_msg("Enter function name: ")
                func = manager.get_function(name)
                if not func:
                    await send_msg("Function not found.")
                else:
                    args = {}
                    for inp in func['inputs']:
                        val_str = await read_msg(f"Enter value for {inp}: ")
                        try:
                            args[inp] = float(val_str)
                        except ValueError:
                            await send_msg("Invalid number.")
                            break
                    else:
                        try:
                            result = manager.execute_function(name, args)
                            await send_msg(f"Result: {result}")
                        except ValueError as e:
                            await send_msg(f"Error: {e}")

            elif choice == '7':
                await send_msg("Goodbye!")
                break
            
            else:
                await send_msg("Invalid option.")

    except (ConnectionResetError, BrokenPipeError, ConnectionError) as e:
        print(f"TCP connection with {addr} closed: {e}")
    except Exception:
        # Log the full traceback instead of silently swallowing the error,
        # so unexpected failures remain diagnosable.
        print(f"Unexpected error while handling TCP client {addr}:")
        traceback.print_exc()
    finally:
        print(f"Closing connection from {addr}")
        writer.close()
        await writer.wait_closed()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start TCP Server
    tcp_server = await asyncio.start_server(handle_tcp_client, '127.0.0.1', 8888)
    addr = tcp_server.sockets[0].getsockname()
    print(f"TCP CLI Server listening on {addr}")
    
    yield
    
    tcp_server.close()
    await tcp_server.wait_closed()


app = FastAPI(title="Function Manager API", lifespan=lifespan)

@app.post("/functions")
async def create_function(func: FunctionCreate):
    try:
        return manager.create_function(func.name, func.inputs, func.outputs, func.expression)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/functions")
async def list_functions():
    return manager.list_functions()

@app.get("/functions/{name}")
async def get_function(name: str):
    func = manager.get_function(name)
    if not func:
        raise HTTPException(status_code=404, detail="Function not found")
    return func

@app.put("/functions/{name}")
async def update_function(name: str, func: FunctionCreate):
    try:
        return manager.update_function(name, func.inputs, func.outputs, func.expression)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.delete("/functions/{name}")
async def delete_function(name: str):
    if manager.delete_function(name):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Function not found")

@app.post("/functions/{name}/execute")
async def execute_function(name: str, payload: FunctionExecute):
    try:
        result = manager.execute_function(name, payload.args)
        return {"result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)

