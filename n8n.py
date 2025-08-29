"""
adnoc n8n pipe
"""

from typing import Optional, Callable, Awaitable
from pydantic import BaseModel, Field
import time
import requests
from fastapi import Request
import json
from azure.cosmos import CosmosClient
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


def extract_oauth_id_token(text):
    # Use regex to find the value of oauth_id_token
    match = re.search(r"oauth_id_token=([^;]+)", text)
    if match:
        return match.group(1)
    else:
        return None


def extract_event_info(event_emitter) -> tuple[Optional[str], Optional[str]]:
    if not event_emitter or not event_emitter.__closure__:
        return None, None
    for cell in event_emitter.__closure__:
        if isinstance(request_info := cell.cell_contents, dict):
            chat_id = request_info.get("chat_id")
            message_id = request_info.get("message_id")
            return chat_id, message_id
    return None, None


class Pipe:
    class Valves(BaseModel):
        n8n_url: str = Field(default="https://adarmesh20.app.n8n.cloud/webhook-test/89eb153f-fa56-4881-be76-50d65dd55337")
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

        endpoint = "https://dbadnocgpt.documents.azure.com:443/"
        key = ""
        database_name = "my-database"
        container_name = "my-container"

        self.client = CosmosClient(endpoint, key)
        self.container = self.client.get_database_client(database_name).get_container_client(container_name)
        self.seen_statuses = set()

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
        chat_id, _ = extract_event_info(__event_emitter__)
        messages = body.get("messages", [])

        #oauth_id_token = extract_oauth_id_token(str(__request__.headers["cookie"]))

        # Verify a message is available
        if messages:
            question = messages[-1]["content"]
            try:
                # Invoke N8N workflow
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
                # payload[self.valves.input_field] = question
                response = requests.post(
                    self.valves.n8n_url, json=payload, headers=headers, timeout=120
                )

                # while response status isn't 200, you need to fetch statuses from CosmosDB and emit them
                while True:
                    # Query latest status from Cosmos DB
                    query = f"SELECT TOP 1 * FROM c WHERE c.session_id = '{chat_id}' ORDER BY c._ts DESC"
                    # query = f"SELECT TOP 1 * FROM c ORDER BY c._ts DESC"
                    items = list(self.container.query_items(query=query, enable_cross_partition_query=True))
                    if items:
                        latest_status = items[0]
                        agent_name = latest_status['agent_name']
                        print(latest_status)
                        # Emit the latest status
                        if self.valves.enable_status_indicator:
                            await self.emit_status(__event_emitter__, "info", f"Latest status: {agent_name}", False)
                            self.seen_statuses.add(latest_status["id"])
                    else:
                        if self.valves.enable_status_indicator:
                            await self.emit_status(__event_emitter__, "info", "Thinking...", False)
                    # Add a termination condition here if needed, else keep polling
                    await asyncio.sleep(self.valves.emit_interval)

                n8n_response = response.json()[self.valves.response_field]
                body["messages"].append({"role": "assistant", "content": n8n_response})
            except Exception as e:
                await self.emit_status(
                    __event_emitter__,
                    "error",
                    f"Error during sequence execution: {str(e)}",
                    True,
                )
                return {"error": str(e)}
        # If no message is available alert user
        else:
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

        # Initialize variables
        text_response = None

        data = n8n_response
        # Iterate through contentItems to find text and highcharts
        for item in data:
            if item["type"] == "text":
                text_response = item["value"]

        await self.emit_status(
            __event_emitter__, "info", f"Complete  ({time.time() - start:.2f}s)", True
        )
        return str(text_response)
 