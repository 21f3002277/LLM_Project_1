from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse
from folder.tasks import execute_task
import os

app = FastAPI()

@app.post("/run")
async def run_task(task: str = Query(..., description="The task description")):
    try:
        result = execute_task(task)
        return {"status": "success", "result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/read")
async def read_file(path: str = Query(..., description="The file path to read")):
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
    with open(path, "r") as file:
        content = file.read()
    return PlainTextResponse(content)