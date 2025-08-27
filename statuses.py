from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import requests
from pprint import pprint
from typing import Optional, Callable, Awaitable
from fastapi import Request


def pipe(
        self,
        body: dict,
        __request__: Request,
        __user__: Optional[dict] = None,
        __event_emitter__: Callable[[dict], Awaitable[None]] = None,
        __event_call__: Callable[[dict], Awaitable[dict]] = None,
    ):
        pprint(body)
        # {
        #     "messages":[
        #         {
        #             "content":"brent price 2025",
        #             "role":"user"
        #         }
        #     ],
        #     "model":"proxyopenai.gpt-4",
        #     "stream":true
        # }

        pprint(__user__)
        # {'api_key': None,
        # 'bio': None,
        # 'created_at': 1756191606,
        # 'date_of_birth': None,
        # 'email': 'darmesh.aidar@gmail.com',
        # 'gender': None,
        # 'id': '62070d2a-d083-41bb-a971-6f9475640800',
        # 'info': None,
        # 'last_active_at': 1756294138,
        # 'name': 'Adam',
        # 'oauth_sub': None,
        # 'profile_image_url': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAGQAAABkCAYAAABw4pVUAAAFG0lEQVR4AeyaTWgdVRTHz9yZN2milDRJG6HBIG1ao5iPCiqIUHUh2IULP/BrIagrUQtqde1OQVBBF6ILvwq6cFFBcGE3unGjRgIaLS21VWj9amueMW/mzTh3itO5byY36TR35lz7f+S+d885c+897//jzJu5E/HXm0MxGh8NBOHFSgEAYYWDCEAAhJkCzNJBhQAIMwWYpYMKARBmCjBLBxVyUQBh9iVtSgcVwowWgAAIMwWYpYMKARBmCjBLBxUCIMwUYJYOKgRAmCnALB2bKoSZdGbSARAzulaeFUAqS2dmIICY0bXyrABSWTozAwHEjK6VZwWQytKZGQggZnStPCuAVJbOzEAAMaNr5VkBpLJ0ZgYCiBldK88KIJWlMzPQbiBuH7mX3ag0MTJtRqmaZrUaiD+7j/r3HFDawB0Hyekbqkm+9V/GaiCtHfeXKuJP7y312+C0FogYupqc/i2lGnvb7yn12+C0Foi/67kV9XX6N5MY3LlinHPAWiDe2K1aXf3ZZ7RxrkErgXjb7iJKrrAUUcMlxXQvv02xbTGsBOJPPa7oG7d/puDQB4rP8QbIXaWKlAHra1SezTogjr+R5A96/hsHC+9RMPdK3pX2/ekn00+b3qwD0kovaZ2cxjEF869RtPgTxX+fyPmJ3C3XEzku2fSyD8jEA4q+0e/zFAft1Bce/ij9zN6ER63JhzLTho5VQMTwVHLvMaLo2pl/PbM73xZPW63JR7K4DR2rgPi7nlU1jToUHvow88VLv1K8eCyzZUcMTiRbKYOya0WzCog3dosiaveXzxVbGkEOkLSJHGpNPUG2vKwB4k3cSyR8RdfONy8ptjSC3ClM2rK1Ju6TH1Y0a4D41zymCBp3TlP3xJeKTxrx8imKzhyW3azJPS+RnLoyB+OOFUDkdrrYNKnIGB45oNh5I/zh/byZ9v2Zp9NP7m9WADm7ne4oWkanfyRv252lLV76TTlWGu747fKDfdMC4ZJ9+vvRk0zfdc/Tht1vlLa+m4qXv+lWytabe2bhZ7IHIkZmyNkwvC7Kna20dZnK2CTsgRTuPS5ACnf0BuK+lcIbiCPI27qb8i/5+xAsvEtradGf3+WHEsmtlJ0Pqj5mFmsg6f1D773H1y/Q8hd719T+OfhwQe7WVY8WfJwcvIH03HtQFFLw/dtr1i86tUDx8h/K8WLTlSS38BUnI4MtEPlDLgZ3KFJ1TyY3gnFX8a1mhEc/6TlEbqXwfU7CFog/81QipJO0c3+dkodQ56LlvWDu5UIgPRUWvDwcbIF42+9WFUqemXePf6b61mBFZ46QvBDIH+oMjJLYeEXexabPEoi7+VqS2yV5lcJjn+bN8+qHRz8uHO/P7iv4ODgaALL61y679+h89eLqA1c4Iph7tRBxx/cUfBwcLIGI0eRZeE4decqJkiumnOu8uunz9qWTyhindQk5l44pPg4GSyDtd8Zp8a3hrLX3X/h/Ibb3T2bz/Td3vHicAwMlB5ZAlAwvMgNAmAEHEABhpgCzdFAhAMJMAWbpoEIAxIwC/5dZUSHMSAIIgDBTgFk6qBAAYaYAs3RQIQDCTAFm6aBCAISZAszSQYVogdQfBJD6NdeuCCBaeeoPAkj9mmtXBBCtPPUHAaR+zbUrAohWnvqDAFK/5toVAUQrT/1BAKlfc+2KAKKVx0xQNyuA6NRpIAYgDYiuWxJAdOo0EAOQBkTXLQkgOnUaiAFIA6LrlgQQnToNxACkAdF1S/4LAAD//46LLyoAAAAGSURBVAMA1r8CZ5q/on8AAAAASUVORK5CYII=',
        # 'role': 'admin',
        # 'settings': {'ui': {'params': {}, 'version': '0.6.25'}},
        # 'updated_at': 1756191606,
        # 'username': None}

        pprint(__request__)
        # <starlette.requests.Request object at 0x3340a6480>

        pprint(__event_emitter__)
        # <function get_event_emitter.<locals>.__event_emitter__ at 0x3317fbc40>

        pprint(__event_call__)
        # <function get_event_call.<locals>.__event_caller__ at 0x3317f9260>
