from enum import Enum
from dataclasses import dataclass
from openai import OpenAI
import openai

from src.basicInfo import info_map

from src.moderation import moderate_message
from typing import Optional, List
from src.constants import (
    BOT_INSTRUCTIONS,
    BOT_NAME,
    EXAMPLE_CONVOS,
)
import discord
from src.base import Message, Prompt, Conversation
from src.utils import split_into_shorter_messages, close_thread, logger
from src.moderation import (
    send_moderation_flagged_message,
    send_moderation_blocked_message,
)

MY_BOT_NAME = BOT_NAME
MY_BOT_EXAMPLE_CONVOS = EXAMPLE_CONVOS

class CompletionResult(Enum):
    OK = 0
    TOO_LONG = 1
    INVALID_REQUEST = 2
    OTHER_ERROR = 3
    MODERATION_FLAGGED = 4
    MODERATION_BLOCKED = 5


@dataclass
class CompletionData:
    status: CompletionResult
    reply_text: Optional[str]
    status_text: Optional[str]


async def generate_completion_response(
    messages: List[Message], user: str
) -> CompletionData:
    try:
        client = OpenAI(
            api_key = openai.api_key
        )

        prompt = Prompt(
            header=Message(
                "System", f"Instructions for {MY_BOT_NAME}: {BOT_INSTRUCTIONS}"
            ),
            examples=MY_BOT_EXAMPLE_CONVOS,
            convo=Conversation(messages + [Message(MY_BOT_NAME)]),
        )
        rendered = prompt.render()

        content_text = ("You are a helpful assistant that talks like a person named Jeffrey. "
                        + "You have the following information as your helpful context but if the question is outside of the information provided, answer the question generally. you do not need to answer everything based on the context given : \n\n"
                        + info_map["basic"] + " | And here comes the information for my recent life: "
                        + info_map["advanced"] + info_map["advanced_last3"] + info_map["advanced_last2"] + info_map["advanced_last1"]
                        + "\n\nyou do not need to answer everything based on the context given."
        )

        response = client.chat.completions.create(
            model="ft:gpt-3.5-turbo-0613:personal:jeffrey-model:8DyiLSXo",
            messages=[
                {
                    "role": "system",
                    "content": content_text
                },
                {
                    "role": "user", "content": rendered
                },
            ],
        )

        reply = response.choices[0].message.content.strip()
        if reply:
            flagged_str, blocked_str = moderate_message(
                message=(rendered + reply)[-500:], user=user
            )
            if len(blocked_str) > 0:
                return CompletionData(
                    status=CompletionResult.MODERATION_BLOCKED,
                    reply_text=reply,
                    status_text=f"from_response:{blocked_str}",
                )

            if len(flagged_str) > 0:
                return CompletionData(
                    status=CompletionResult.MODERATION_FLAGGED,
                    reply_text=reply,
                    status_text=f"from_response:{flagged_str}",
                )

        return CompletionData(
            status=CompletionResult.OK, reply_text=reply, status_text=None
        )
    except openai.APIError as e:
        if "This model's maximum context length" in e.user_message:
            return CompletionData(
                status=CompletionResult.TOO_LONG, reply_text=None, status_text=str(e)
            )
        else:
            logger.exception(e)
            return CompletionData(
                status=CompletionResult.INVALID_REQUEST,
                reply_text=None,
                status_text=str(e),
            )
    except Exception as e:
        logger.exception(e)
        return CompletionData(
            status=CompletionResult.OTHER_ERROR, reply_text=None, status_text=str(e)
        )


async def process_response(
    user: str, thread: discord.Thread, response_data: CompletionData
):
    status = response_data.status
    reply_text = response_data.reply_text
    status_text = response_data.status_text
    if status is CompletionResult.OK or status is CompletionResult.MODERATION_FLAGGED:
        sent_message = None
        if not reply_text:
            sent_message = await thread.send(
                embed=discord.Embed(
                    description=f"**Invalid response** - empty response",
                    color=discord.Color.yellow(),
                )
            )
        else:
            shorter_response = split_into_shorter_messages(reply_text)
            for r in shorter_response:
                sent_message = await thread.send(r)
        if status is CompletionResult.MODERATION_FLAGGED:
            await send_moderation_flagged_message(
                guild=thread.guild,
                user=user,
                flagged_str=status_text,
                message=reply_text,
                url=sent_message.jump_url if sent_message else "no url",
            )

            await thread.send(
                embed=discord.Embed(
                    description=f"⚠️ **This conversation has been flagged by moderation.**",
                    color=discord.Color.yellow(),
                )
            )
    elif status is CompletionResult.MODERATION_BLOCKED:
        await send_moderation_blocked_message(
            guild=thread.guild,
            user=user,
            blocked_str=status_text,
            message=reply_text,
        )

        await thread.send(
            embed=discord.Embed(
                description=f"❌ **The response has been blocked by moderation.**",
                color=discord.Color.red(),
            )
        )
    elif status is CompletionResult.TOO_LONG:
        await close_thread(thread)
    elif status is CompletionResult.INVALID_REQUEST:
        await thread.send(
            embed=discord.Embed(
                description=f"**Invalid request** - {status_text}",
                color=discord.Color.yellow(),
            )
        )
    else:
        await thread.send(
            embed=discord.Embed(
                description=f"**Error** - {status_text}",
                color=discord.Color.yellow(),
            )
        )


async def process_response_file(
    user: str, thread: discord.Thread, response_file: str
):
    # status = response_data.status
    # reply_text = response_data.reply_text
    # status_text = response_data.status_text

    # send back audio file
    print("response_file_path: ", response_file)
    await thread.send(file=discord.File(response_file))

    # if status is CompletionResult.OK or status is CompletionResult.MODERATION_FLAGGED:
    #     sent_message = None
    #     if not reply_text:
    #         sent_message = await thread.send(
    #             embed=discord.Embed(
    #                 description=f"**Invalid response** - empty response",
    #                 color=discord.Color.yellow(),
    #             )
    #         )
    #     else:
    #         shorter_response = split_into_shorter_messages(reply_text)
    #         for r in shorter_response:
    #             sent_message = await thread.send(r)
    #     if status is CompletionResult.MODERATION_FLAGGED:
    #         await send_moderation_flagged_message(
    #             guild=thread.guild,
    #             user=user,
    #             flagged_str=status_text,
    #             message=reply_text,
    #             url=sent_message.jump_url if sent_message else "no url",
    #         )

    #         await thread.send(
    #             embed=discord.Embed(
    #                 description=f"⚠️ **This conversation has been flagged by moderation.**",
    #                 color=discord.Color.yellow(),
    #             )
    #         )
    # elif status is CompletionResult.MODERATION_BLOCKED:
    #     await send_moderation_blocked_message(
    #         guild=thread.guild,
    #         user=user,
    #         blocked_str=status_text,
    #         message=reply_text,
    #     )

    #     await thread.send(
    #         embed=discord.Embed(
    #             description=f"❌ **The response has been blocked by moderation.**",
    #             color=discord.Color.red(),
    #         )
    #     )
    # elif status is CompletionResult.TOO_LONG:
    #     await close_thread(thread)
    # elif status is CompletionResult.INVALID_REQUEST:
    #     await thread.send(
    #         embed=discord.Embed(
    #             description=f"**Invalid request** - {status_text}",
    #             color=discord.Color.yellow(),
    #         )
    #     )
    # else:
    #     await thread.send(
    #         embed=discord.Embed(
    #             description=f"**Error** - {status_text}",
    #             color=discord.Color.yellow(),
    #         )
    #     )
