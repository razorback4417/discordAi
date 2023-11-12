from openai import OpenAI
import openai

# Set your OpenAI API key here
# You can also set it as an environment variable and use: openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = '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'

client = OpenAI(
    api_key = openai.api_key
)


# model =  "ft:gpt-3.5-turbo-1106:personal::8JuO1d20
completion = client.chat.completions.create(
  model="ft:gpt-3.5-turbo-0613:personal:jeffrey-model:8DyiLSXo",
  messages=[
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hi?"},
  ]
)

print(completion.choices[0].message.content)