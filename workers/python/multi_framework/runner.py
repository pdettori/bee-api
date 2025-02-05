# Copyright 2024 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from bullmq import Job
from opentelemetry import trace

from workers import create_worker
from database import database
from workers import redis_client
import json

from bee_hive.langgraph_agent import LangGraphAgent
from bee_hive.agent_factory import AgentFramework, AgentFactory  # Adjust 'your_module' to where your classes are defined
import traceback

tracer = trace.get_tracer("job-trace")

logger = logging.getLogger()

RUN_QUEUE_NAME = "runs-lg"


# langgraph example config
agent_configuration = {
  "apiVersion": "beehive/v1alpha1",
  "kind": "Agent",
  "metadata": {
    "name": "langgraph.math_agent.MathAgent.getGraph",
    "labels": {
      "app": "langgraph-test"
    }
  },
  "spec": {
    "model": "llama3.1:latest",
    "description": "test",
    "instructions": "you are a math wizard",
    "framework": "langgraph"
  }
}

async def handleRun(job: Job, job_token):
    # TODO remove tracing once BULLMQ has instrumentation
    with tracer.start_as_current_span("job") as span:
        data = job.data
        print(data)
        runId = data.get('runId')
        if runId is None:
            raise RuntimeError("runId not found")

        run = await database.get_collection('run').find_one({"_id": runId})
        if run is None:
            raise RuntimeError("Run not found")
        
        print(run)

        threadId = run["thread"]
        if threadId is None:
            raise RuntimeError("threadId not found")

        messages = await database.get_collection('message').find_one({"thread": threadId})
        if run is None:
            raise RuntimeError("Thread not found")
        
        print(messages)

        thread_run_created_event = {
            "event": "thread.run.created",
            "data": {
                "id": runId,
                "status": "created",
                "timestamp": "2023-10-05T14:48:00Z",
                "initiator": "user@example.com",
                "details": {
                    "description": "thread run started",
                    "priority": "high",
                    "message": messages['content']
                }
            }
        }
        
        await redis_client.publish(f'run:{runId}', json.dumps(thread_run_created_event))

        # Instantiate a LangGraph Agent
        try:
            langgraph_factory = AgentFactory.create_agent(AgentFramework.LANGGRAPH)
            langgraph_agent = langgraph_factory(agent=agent_configuration)
            print("LangGraph agent instantiated successfully.")
        except Exception as e:
            print(f"Error instantiating LangGraphAgent: {e}")
            traceback.print_exc()
        
        output = None
        try:
            output = langgraph_agent.run(messages['content'])
        except Exception as ex:
            print(f"Failed to run LangGraphAgent: {ex}")

        thread_run_completed_event = {
            "event": "thread.run.completed",
            "data": {
                "id": runId,
                "status": "completed",
                "timestamp": "2023-10-05T14:48:00Z",
                "initiator": "user@example.com",
                "details": {
                    "description": "thread run completed",
                    "priority": "high",
                    "message": {"messages": {"content": output}}
                }
            }
        }
        
        await redis_client.publish(f'run:{runId}', json.dumps(thread_run_completed_event))

        thread_run_done_event = {"event": "done", "data": "[DONE]"}

        await redis_client.publish(f'run:{runId}', json.dumps(thread_run_done_event))
       
runWorker = create_worker(RUN_QUEUE_NAME, handleRun, {})
