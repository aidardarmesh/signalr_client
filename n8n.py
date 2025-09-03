"""
adnoc n8n pipe
"""

from typing import Optional, Callable, Awaitable
from pydantic import BaseModel, Field
import time
import requests
from fastapi import Request
import json
from azure.cosmos.aio import CosmosClient
from azure.cosmos.exceptions import CosmosHttpResponseError
import asyncio
import re
import logging
import httpx


# Get the HTTP logging policy logger from the Azure SDK
logger = logging.getLogger("azure.core.pipeline.policies.http_logging_policy")

# Set the logging level to WARNING or ERROR to suppress INFO and DEBUG logs
logger.setLevel(logging.WARNING)

# Alternatively, to disable logging altogether:
# logger.disabled = True


class Pipe:
    class Valves(BaseModel):
        n8n_url: str = Field(default="https://adarmesh20.app.n8n.cloud/webhook/89eb153f-fa56-4881-be76-50d65dd55337")
        n8n_bearer_token: str = Field(default="...")
        input_field: str = Field(default="chatInput")
        # response_field: str = Field(default="contentItems")
        response_field: str = Field(default="output")
        emit_interval: float = Field(
            default=1.0, description="Interval in seconds between status emissions"
        )
        enable_status_indicator: bool = Field(
            default=True, description="Enable or disable status indicator emissions"
        )

    def __init__(self):
        self.type = "pipe"
        self.id = "c1_contracts_uat"
        self.name = "c1 Contracts [UAT]"
        self.valves = self.Valves()
        self.last_emit_time = 0
        self.seen = set()

        self.endpoint = "https://dbadnocgpt.documents.azure.com:443/"
        self.key = "uLO7CKicLpAtRQZD8lyyjE8ccWVAZdcc7pwXXnxeCnBvtAsUihpt2M4y9RVdP8heavPrypPT9F5XACDbE9poVw=="
        self.database_name = "my-database"
        self.container_name = "my-container"

    async def pipe(
        self,
        body: dict,
        __request__: Request,
        __user__: Optional[dict] = None,
        __event_emitter__: Callable[[dict], Awaitable[None]] = None,
        __event_call__: Callable[[dict], Awaitable[dict]] = None,
    ) -> Optional[dict]:
        start = time.time()
        await self.emit_status(
            __event_emitter__, "info", "/Calling N8N Workflow...", False
        )
        chat_id, _ = await extract_event_info(__event_emitter__)
        messages = body.get("messages", [])

        #oauth_id_token = await extract_oauth_id_token(str(__request__.headers["cookie"]))

        if not messages:
            await self.emit_status(
                __event_emitter__,
                "error",
                "No messages found in the request body",
                True,
            )
            body["messages"].append(
                {
                    "role": "assistant",
                    "content": "No messages found in the request body",
                }
            )

        question = messages[-1]["content"]
        n8n_response = None

        post_n8n_task = asyncio.create_task(self.post_n8n_workflow(question, chat_id, __user__))
        status_polling_task = asyncio.create_task(self.poll_cosmos(chat_id, __event_emitter__))

        try:
            # Wait for the POST task to complete
            n8n_response = await post_n8n_task
        finally:
            # Ensure polling task is cancelled regardless of what happens
            if not status_polling_task.done():
                status_polling_task.cancel()
                # Wait for cancellation to complete with a timeout
                try:
                    await asyncio.wait_for(status_polling_task, timeout=2.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    # If we hit timeout, the task might be stuck
                    pass

        # Initialize variables
        #text_response = None
        text_response = n8n_response.get(self.valves.response_field, "No response field found")

        # data = n8n_response
        # # Iterate through contentItems to find text and highcharts
        # for item in data:
        #     if item["type"] == "text":
        #         text_response = item["value"]

        await self.emit_status(
            __event_emitter__, "info", f"Complete  ({time.time() - start:.2f}s)", True
        )
        return str(text_response)
    
    async def post_n8n_workflow(self, question, chat_id, __user__):
        headers = {
            # "Authorization": "Basic <KEY>",
            "Content-Type": "application/json",
        }
        payload = {
            "input": {
                "conversationId": f"{chat_id}",
                "user": json.dumps(__user__["email"]),
                #"oauth_id_token": oauth_id_token,
                "message": question,
            }
        }
        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(self.valves.n8n_url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            return response.json()

    async def poll_cosmos(self, chat_id, __event_emitter__):
        try:
            async with CosmosClient(self.endpoint, self.key) as cosmos_client:
                database = cosmos_client.get_database_client(self.database_name)
                container = database.get_container_client(self.container_name)

                while True:
                    # Check for cancellation at each iteration
                    if asyncio.current_task().cancelled():
                        return

                    query = f"SELECT TOP 1 * FROM c WHERE c.session_id = '{chat_id}' ORDER BY c._ts DESC"
                    items = []
                    try:
                        items_async_iterable = container.query_items(query=query)
                        items = [item async for item in items_async_iterable]
                    except CosmosHttpResponseError as e:
                        await self.emit_status(__event_emitter__, "error", f"Cosmos query error: {str(e)}", False)
                    
                    if items:
                        latest_status = items[0]
                        if latest_status["id"] in self.seen:
                            continue
                        
                        self.seen.add(latest_status["id"])
                        agent_name = latest_status["agent_name"]
                        print(agent_name)
                        await self.emit_status(__event_emitter__, "info", f"Latest status: {agent_name}", False)
                    else:
                        await self.emit_status(__event_emitter__, "info", "Thinking...", False)
                    await asyncio.sleep(self.valves.emit_interval)
        except asyncio.CancelledError:
            # Just allow the cancellation to propagate up
            # This ensures the context manager closes properly
            raise

    async def emit_status(
        self,
        __event_emitter__: Callable[[dict], Awaitable[None]],
        level: str,
        message: str,
        done: bool,
    ):
        current_time = time.time()
        if (
            __event_emitter__
            and self.valves.enable_status_indicator
            and (
                current_time - self.last_emit_time >= self.valves.emit_interval or done
            )
        ):
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "status": "complete" if done else "in_progress",
                        "level": level,
                        "description": message,
                        "done": done,
                    },
                }
            )
            self.last_emit_time = current_time
 

async def extract_oauth_id_token(text):
    # Use regex to find the value of oauth_id_token
    match = re.search(r"oauth_id_token=([^;]+)", text)
    if match:
        return match.group(1)
    else:
        return None


async def extract_event_info(event_emitter) -> tuple[Optional[str], Optional[str]]:
    if not event_emitter or not event_emitter.__closure__:
        return None, None
    for cell in event_emitter.__closure__:
        if isinstance(request_info := cell.cell_contents, dict):
            chat_id = request_info.get("chat_id")
            message_id = request_info.get("message_id")
            return chat_id, message_id
    return None, None