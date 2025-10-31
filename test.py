import openai
from pprint import pprint

client = openai.OpenAI()

batches = client.batches.list()

for batch in batches:
    pprint(batch.model_dump_json())