import os
import json
import requests
import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
from dotenv import load_dotenv
from subprocess import run, CalledProcessError
import uuid  # For generating unique filenames

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Response format for the LLM
response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "task_runner",
        "schema": {
            "type": "object",
            "required": ["python_dependencies", "python_code"],
            "properties": {
                "python_code": {
                    "type": "string",
                    "description": "Python code to perform the task"
                },
                "python_dependencies": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "module": {
                                "type": "string",
                                "description": "Name of python module"
                            }
                        },
                        "required": ["module"],
                        "additionalProperties": False
                    }
                }
            }
        }
    }
}

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

AIPROXY_TOKEN = os.getenv("AIPROXY_TOKEN")
if not AIPROXY_TOKEN:
    raise ValueError("AIPROXY_TOKEN environment variable is not set")

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {AIPROXY_TOKEN}"
}

@app.get("/")  # Root route
def home():
    return "LLM Project Server is Running..................."

@app.post("/run")
def task_runner(task: str = Query(..., description="Plain-English task description")):
    url = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    
    # Prompt for the LLM
    prompt = """
    You are an advanced Automation Agent that dynamically generates code to execute multi‑step tasks described in plain English. Your output must produce processing artifacts that exactly match pre‑computed expected results. Follow these instructions rigorously:

    1. **Security & Data Boundaries**
        - **Data Access:** Only read from and write to files under the `/data` directory. Do not access, exfiltrate, or refer to any data outside this directory.
        - **File Integrity:** Under no circumstances delete or remove any files from the file system.

    2. **Task Parsing & Identification**
        - Analyze the plain‑English task description provided.
        - Identify the specific operations (e.g., installing dependencies, formatting files, counting dates, sorting JSON arrays, executing SQL queries, extracting email, extracting text from image etc.) or business tasks (e.g., fetching from an API, scraping a website, cloning a git repo, image processing, etc.).
        - If multiple operations are implied, break them down into clear, deterministic steps.

    3. **Dynamic Code Generation**
        - For each identified step, generate well‑structured, deterministic code (e.g., shell commands, Python scripts, SQL queries) that can be executed to produce exactly verifiable results.
        - When an LLM call is required (e.g., to extract an email address from text or a credit card number from an image), include a clearly defined interface call or simulated function that encapsulates the LLM invocation.
        - **LLM Integration Details:** When the task requires passing data to an LLM for extraction, use the URL "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions" with model is "gpt-4o-mini". For embedding operations, use the URL "http://aiproxy.sanand.workers.dev/openai/v1/embeddings" with model "text-embedding-3-small". In both cases, retrieve the API key from the environment using `AIPROXY_TOKEN = os.environ["AIPROXY_TOKEN"]`.
        - Include comments and clear variable names to show the mapping from the task description to the generated code steps.

    4. **Execution & Verification**
        - Ensure the generated code writes output only to specified files under `/data`.
        - The final artifacts (files) must exactly match the expected outputs determined by pre‑computed results.
        - Include brief inline explanations where necessary to explain non‑obvious steps, but keep extraneous commentary to a minimum.

    5. **Response Format**
        - Your answer must include the complete code and any configuration needed to run the solution.
        - Do not provide external commentary beyond what is required to understand the code structure.
        - Always verify that your generated solution adheres to the security constraints and file system boundaries.

    **Now, process the following task description:**

    {task}

    Note: When executing any uv script, use the command format `uv run <script_name> <arguments>`.
    
    **The output should be well‑organized as follows**:
    1. <Inline_metadata_script> (eg.
    # /// script
    # required‑python = ">=3.11"  # Python version requirement
    # dependencies = [            # EXACT PyPI package names
    #     "numpy",
    #     "scikit‑learn",         # Never use 'sklearn'
    #     "requests"
    # ]
    # description = "Task description for documentation"  # Single purpose description
    # ///
    )
    
    2. Note: **<gap of five lines must>**
      
    3. Note: <import all the python dependencies> then two line gap
      
    4. <code for the task to get implemented>
            
    **Notes must is implemented**
    
    If the task is to Count the number of given weekdays from a text file of dates and save the count to another file does not
    use the approach of not using datetime module use another approach as the file contains formats = [
        "%d-%b-%Y", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d", "%b %d, %Y", 
        "%d-%b-%Y", "%Y/%m/%d", "%Y-%m-%d %H:%M:%S", "%b %d, %Y",
        "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %I:%M:%S"]  
        
    If the task format a file using prettier the shell should not True   
    
    Understand the task carefully what it want then do as it
    Note: if the task ask for sender-email Here’s a clean and effective prompt that ensures only the sender’s email is extracted without including unnecessary instructions in the output:

"Find and return only the sender's email address from the following text:"

This keeps the prompt clear while ensuring the output is just the extracted sender's email. If you're using this in a script or automation, make sure the extraction logic correctly isolates the sender's email without adding extra text.
    Note: if the task ask for extract the credit card number by Passing the image to an LLM, have it extract the card number, and write it without spaces to than it should extract the numbers only(eg.prompt: Extract all the text correctly from the image, focusing on the longest continuous string of numbers.
    and payload(in sample format) : {
  "model": "gpt-4o-mini",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Extract the 16 digit numeric string from the image, focusing on the longest continuous string of characters."},
        {
          "type": "image_url",
          "image_url": { "url": "data:image/png;base64,$IMAGE_BASE64" }
        }
      ]
    }
  ]
})

    Note: Compute Similarity:
    Convert the list of embeddings into a NumPy array.
    Use a cosine similarity function (e.g., cosine_similarity from scikit-learn or a custom implementation) to compute a similarity matrix for all pairs of comment embeddings.
    Exclude self-similarity by setting the diagonal of the similarity matrix to -1.
    Find the pair of comments with the highest cosine similarity (i.e., the most similar pair).
    
    be careful it is compulsory to execute each task within 15 second timer and 
    """

    max_retries = 4
    attempts = 0
    success = False
    last_error = None
    previous_code = None

    # Generate a unique filename for this task
    task_id = str(uuid.uuid4())  # Generate a unique ID for the task
    script_filename = f"llm_{task_id}.py"  # Unique filename for each task

    while attempts < max_retries and not success:
        try:
            messages = []
            if attempts == 0:
                messages = [
                    {"role": "user", "content": task},
                    {"role": "system", "content": prompt}
                ]
            else:
                messages = [
                    {"role": "user", "content": task},
                    {"role": "system", "content": prompt},
                    {"role": "assistant", "content": previous_code},
                    {"role": "user", "content": f"Execution failed with error: {last_error}. Please correct the code."}
                ]

            data = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "response_format": response_format
            }

            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()

            content_str = result['choices'][0]['message']['content']
            content = json.loads(content_str)
            python_dependencies = content['python_dependencies']
            python_code = content['python_code']
            previous_code = content_str

            # Generate metadata script
            Inline_metadata_script = f"""
            # /// script
            # required-python = ">=3.11"
            # description = [
            {''.join(f"# \"{dependency['module']}\",\n" for dependency in python_dependencies)}# ]
            # ///
            # """

            # Write the generated code to a unique file
            with open(script_filename, 'w') as f:
                f.write(Inline_metadata_script)
                f.write("\n\n\n")
                f.write(python_code)

            # Execute code
            output = run(["uv", "run", script_filename], capture_output=True, text=True, cwd=os.getcwd())

            if output.returncode == 0:
                success = True
                logger.info("Execution succeeded")
            else:
                last_error = output.stderr
                logger.error(f"Attempt {attempts+1} failed: {last_error}")
                attempts += 1

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            last_error = "Invalid response format from LLM"
            attempts += 1
        except KeyError as e:
            logger.error(f"Missing key in response: {str(e)}")
            last_error = "Invalid response structure from LLM"
            attempts += 1
        except requests.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise HTTPException(status_code=500, detail="AI Proxy communication error")
        except CalledProcessError as e:
            logger.error(f"Subprocess execution failed: {str(e)}")
            last_error = e.stderr
            attempts += 1
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            last_error = str(e)
            attempts += 1

    if not success:
        raise HTTPException(
            status_code=500,
            detail=f"Task failed after {max_retries} attempts. Last error: {last_error}"
        )

    return {"status": "success", "output": output.stdout, "script_filename": script_filename}

@app.get("/read", response_class=PlainTextResponse)
def task_reader(path: str = Query(..., description="Path to the file to read")):
    # Ensure the path is within the allowed directory
    allowed_directory = "/data"
    if not path.startswith(allowed_directory):
        raise HTTPException(status_code=403, detail="Access outside /data is not allowed")

    try:
        with open(path, 'r') as file:
            content = file.read().strip()
            return content
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
