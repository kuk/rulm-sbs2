
import re
import sys
import uuid
import random
import json
import asyncio
import pickle
import html
import time
from dataclasses import dataclass
from contextlib import redirect_stdout
from collections import (
    Counter,
    defaultdict
)

from tqdm import tqdm

import numpy as np
import pandas as pd

from matplotlib import pyplot as plt

import aiohttp

import openai
import label_studio_sdk


#####
#
#   JSON
#
#####


def write_json(path, data):
    with open(path, 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def read_json(path):
    with open(path) as file:
        return json.load(file)


def write_jsonl(path, items):
    with open(path, 'w') as file:
        for item in items:
            file.write(json.dumps(item, ensure_ascii=False))
            file.write('\n')


def read_jsonl(path):
    with open(path) as file:
        for line in file:
            yield json.loads(line)


#######
#
#   PICKLE
#
#####


def read_pickle(path):
    with open(path, 'rb') as file:
        return pickle.load(file)
    
    
def write_pickle(path, obj):
    with open(path, 'wb') as file:
        pickle.dump(obj, file)


######
#
#   UID
#
#####


def gen_uid():
    return str(uuid.uuid4())


########
#
#   DOTENV
#
#######


def read_dotenv(path):
    with open(path) as file:
        for line in file:
            if '=' in line:
                yield line.rstrip('\n').split('=', 1)


#######
#
#   HEADERS
#
#####


# Host: developers.sber.ru
# Origin: https://developers.sber.ru
# Pragma: no-cache


def read_headers(path):
    with open(path) as file:
        for line in file:
            index = line.find(': ')
            if index > 0:
                line = line.rstrip('\n')
                yield line[:index], line[index + 2:]


# sticky_cookie_dp=2668b030f58b3efd; sticky_cookie_km=f5e5454e6e94ffe5; CRON=acff5ee7c28c708c6ffe998ee063f47a; sticky_cookie_cgw=d1d5685d6e85368d


def parse_cookies(value):
    for part in value.split('; '):
        yield part.split('=', 1)


#####
#
#   VICUNA
#
#######


# {'question_id': 1,
#  'text': 'How can I improve my time management skills?',
#  'category': 'generic'}


def parse_vicuna(items):
    for item in items:
        yield {
            'id': gen_uid(),
            'source': 'vicuna',
            'source_id': item['question_id'],
            'category': item['category'],
            'instruction': item['text']
        }


######
#
#   ALPACA
#
######


# {'id': 'user_oriented_task_0',
#  'motivation_app': 'Grammarly',
#  'instruction': 'The sentence you are given might be too wordy, complicated, or unclear. Rewrite the sentence and make your writing clearer by keeping it concise. Whenever possible, break complex sentences into multiple sentences and eliminate unnecessary words.',
#  'instances': [{'input': 'If you have any questions about my rate or if you find it necessary to increase or decrease the scope for this project, please let me know.',
#    'output': "If you have any questions about my rate or find it necessary to increase or decrease this project's scope, please let me know."}]}


def parse_alpaca(items):
    for item in items:

        instruction = item['instruction']
        input = item['instances'][0]['input']
        if input:
            instruction += f'\n\n"{input}"'

        yield {
            'id': gen_uid(),
            'source': 'alpaca',
            'source_id': item['id'],
            'instruction': instruction
        }


#########
#
#   ARENA
#
######


def parse_arena(records):
    for record in records:
        assert len(record.conversation_a) >= 2
        assert len(record.conversation_b) >= 2
        assert record.conversation_a[0]['role'] == record.conversation_b[0]['role'] == 'user'
        assert record.conversation_a[0]['content'] == record.conversation_b[0]['content']

        yield {
            'id': gen_uid(),
            'source': 'arena',
            'source_id': record.question_id,
            'lang': record.language,
            'instruction': record.conversation_a[0]['content']
        }


########
#
#   OPENAI
#
#####


async def openai_singleturn(
        prompt, model,
        temperature=1,
        max_tokens=None,
        request_timeout=60
):
    completion = await openai.ChatCompletion.acreate(
        model=model,
        messages=[{
            'role': 'user',
            'content': prompt
        }],
        temperature=temperature,
        max_tokens=max_tokens,
        request_timeout=request_timeout
    )
    return completion.choices[0].message.content


def openai_embed_batch(texts, model='text-embedding-ada-002'):
    results = openai.Embedding.create(
        input=texts,
        model=model
    )
    return [_.embedding for _ in results.data]


#######
#
#   OPENAI TRANSLATE
#
######


async def openai_translate(instruction):
    prompt = f'''Ты профессиональный переводчик с английского на русский.
Переведи задание для ассистента на русский. Обращайся к ассистенту на ты.

Задание на английском (заключено в [[ ]]):
[[{instruction}]]

Задание на русском:'''
    answer = await openai_singleturn(prompt, model='gpt-3.5-turbo-0613')
    return re.sub(r'\[\[+|\]\]+', '', answer).strip()


#######
#
#   OPENAI SBS
#
######


async def openai_sbs(instruction, answer_a, answer_b):
    prompt = f'''Please act as an impartial judge and evaluate the quality of the responses provided by two AI assistants to the user question displayed below. You should choose the assistant that follows the user's instructions and answers the user's question better. Your evaluation should consider factors such as the helpfulness, relevance, accuracy, depth, creativity, and level of detail of their responses. Begin your evaluation by comparing the two responses and provide a short explanation. Avoid any position biases and ensure that the order in which the responses were presented does not influence your decision. Do not allow the length of the responses to influence your evaluation. Do not favor certain names of the assistants. Be as objective as possible. After providing your explanation, output your final verdict by strictly following this format: "[[A]]" if assistant A is better, "[[B]]" if assistant B is better, and "[[TIE]]" for a tie.

[User Question]
{instruction}

[The Start of Assistant A's Answer]
{answer_a}
[The End of Assistant A's Answer]

[The Start of Assistant B's Answer]
{answer_b}
[The End of Assistant B's Answer]
'''
    return await openai_singleturn(prompt, model='gpt-3.5-turbo-0613')
    

def sbs_answer_result(answer):
    match = re.search(r'\[\[(A|B|TIE)\]\]', answer)
    if match:
        return match.group(1).lower()


def sbs_agg_swap(result_ab, result_ba):
    if result_ab == 'a' and result_ba == 'b':
        return 'a'
    elif result_ab == 'b' and result_ba == 'a':
        return 'b'
    elif result_ab == result_ba == 'tie':
        return 'tie'


def sbs_name_models(text, model_a, model_b):
    def repl(match):
        value = match.group(1)
        assert value in ('A', 'B'), value
        if value == 'A':
            return model_a
        elif value == 'B':
            return model_b

    text = re.sub(r'Assistant (A|B)', repl, text)
    text = re.sub(r'\[\[(A|B)\]\]', repl, text)
    return text


##########
#
#  LABEL STUDIO
#
########


# https://labelstud.io/api
# https://labelstud.io/guide/task_format.html


#######
#
#   LABEL TRANSLATE
#
####


'''
<View>
  <View style="display: grid; grid-template: auto/1fr 1fr">
    <Header value="instruction" />
    <Header value="answer" />

    <Text name="instruction" value="$instruction" />
    <TextArea name="answer" toName="instruction"
              rows="2" editable="true"
              showSubmitButton="false" 
              required="true"/>
  </View>
</View>
'''


def translate_label_item(item):
    return {
        'data': {
            'id': item['id'],
            'instruction': item['instruction'],
        },
        'predictions': [{
            'result': [{
                'from_name': 'answer',
                'to_name': 'instruction',
                'type': 'textarea',
                'value': {
                    'text': [item['answer']]
                }
            }]
        }]
    }


def label_translate_item(item):
    return {
        'id': item['data']['id'],
        'answer': item['annotations'][0]['result'][0]['value']['text'][0]
    }


#######
#
#   LABEL CLASSIFY
#
###


'''
<View>
  <View style="display: grid; grid-template: auto/1fr 1fr">
    <Header value="instruction" />
    <Header value="category" />

    <Text name="instruction" value="$instruction" />

    <Choices name="category" toName="instruction" choice="single" showInline="true">
      <Choice value="brainstorm" />
      <Choice value="reason" />
      <Choice value="qa" />
      <Choice value="closed qa" />
      <Choice value="explain" />

      <Choice value="writing" />
      <Choice value="roleplay" />
      <Choice value="joke" />
      <Choice value="grammar" />
      <Choice value="rewrite" />
      <Choice value="poem" />
      <Choice value="outline" />
      <Choice value="cooking" />

      <Choice value="coding" />
      <Choice value="summary" />
      <Choice value="enumerate" />

      <Choice value="chat" />
      <Choice value="extract" />
      <Choice value="math" />

      <Choice value="bad instruction" />
  </Choices>
  </View>
</View>
'''


def classify_label_item(item):
    return {
        'data': {
            'id': item['id'],
            'instruction': item['instruction'],
        },
        'predictions': [{
            'result': [{
                'from_name': 'category',
                'to_name': 'instruction',
                'type': 'choices',
                'value': {
                    'choices': [item['category']]
                }
            }]
        }]
    }


def label_classify_item(item):
    category = None
    annotation = item['annotations'][0]
    if not annotation['was_cancelled'] and annotation['result']:
        category = annotation['result'][0]['value']['choices'][0]

    return {
        'id': item['data']['id'],
        'category': category
    }


######
#
#   LABEL SBS
#
######


'''
<View>
  <View>
    <Text name="instruction" value="$instruction" />
  </View>

  <View style="display: grid; grid-template: auto/1fr 1fr">
    <Header value="$model_a" />
    <Header value="$model_b" />

    <Text name="answer_a" value="$answer_a" />
    <Text name="answer_b" value="$answer_b" />
  </View>

  <View>
    <Choices name="result" toName="instruction" choice="single" showInline="true">
      <Choice alias="a" value="$model_a"/>
      <Choice alias="b" value="$model_b" />
      <Choice alias="tie" value="tie" />
    </Choices>

    <Header value="ab" />
    <Text name="answer_ab" value="$answer_ab" />

    <Header value="ba" />
    <Text name="answer_ba" value="$answer_ba" />

  </View>
</View>
'''


def sbs_label_item(item):
    return {
        'data': {
            'id': item['id'],
            'model_a': item['model_a'],
            'model_b': item['model_b'],
            'instruction': item['instruction'],
            'answer_a': item['answer_a'],
            'answer_b': item['answer_b'],
            'answer_ab': sbs_name_models(item['answer_ab'], item['model_a'], item['model_b']),
            'answer_ba': sbs_name_models(item['answer_ba'], item['model_b'], item['model_a']),
        },
        'predictions': [{
            'result': [{
                'from_name': 'result',
                'to_name': 'instruction',
                'type': 'choices',
                'value': {
                    'choices': [item['result']]
                }
            }]
        }]
    }


def label_sbs_item(item):
    result = None
    annotation = item['annotations'][0]
    if not annotation['was_cancelled'] and annotation['result']:
        result = annotation['result'][0]['value']['choices'][0]

    return {
        'id': item['data']['id'],
        'model_a': item['data']['model_a'],
        'model_b': item['data']['model_b'],
        'result': result
    }


########
#
#   COSINE SIM
#
######


def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


########
#
#  GIGACHAT
#
#####


@dataclass
class GigachatClient:
    session: ...
    user_id: str
    space_id: str


def gigachat_client_init(headers, timeout=60):
    # Otherwise aiohttp clipping payload?
    headers.pop('Content-Length', None)

    value = headers['Cookie']
    cookies = dict(parse_cookies(value))

    return GigachatClient(
        session=aiohttp.ClientSession(
            headers=headers,
            cookies=cookies,
            timeout=aiohttp.ClientTimeout(total=timeout)
        ),
        user_id=headers['user-id'],
        space_id=headers['space-id'],
    )


async def gigachat_request(client, prompt, session_id, model_type='GigaChat:v1.13.0'):
    response = await client.session.post(
        'https://developers.sber.ru/api/chatwm/api/client/request',
        json={
            'request_json': prompt,
            'session_id': session_id,
            'model_type': model_type,
            'preset': 'default',
            'generate_alternatives': False,
        }
    )
    response.raise_for_status()
    data = await response.json()

    # {
    #     "result": "accepted",
    #     "request_id": "5a9c58ff-bd31-4e97-bb6c-065534f614f4",
    #     "generation_start_estimation_seconds": 0.1415866
    # }
    
    assert data.get('result') == 'accepted', data
    return data['request_id']


async def gigachat_result_events(client, request_id):
    response = await client.session.get(
        'https://developers.sber.ru/api/chatwm/api/client/get_result_events',
        params={
            'request_id': request_id,
            'space-id': client.space_id,
            'user-id': client.user_id,
        },
    )
    response.raise_for_status()

    async for line in response.content:
        # data: {"status":"in_progress","next_update_estimation_seconds":8.0,"model_type":"GigaChat:v1.13.0","model_type_display_name":"GigaChat:v1.13.0","responses":[{"id":6014992,"data":"\xd0\x94\xd1\x80\xd1\x8...xd0\xbd\xd1\x8b\xd0\xb5"}]}\r\n

        line = line.decode('utf8')
        if not line.startswith('data: '):
            continue
            
        line = line[len('data: '):]
        item = json.loads(line)
        yield {
            'status': item['status'],
            'text': item['responses'][0]['data']
        }


async def gigachat_singleturn(client, prompt):
    session_id = gen_uid()
    request_id = await gigachat_request(client, prompt, session_id)
    async for item in gigachat_result_events(client, request_id):
        if item['status'] == 'ready':
            return item['text']


######
#
#   YAGPT
#
#####


# https://cloud.yandex.com/en/docs/yandexgpt/api-ref/TextGeneration/instruct


@dataclass
class YagptClient:
    session: ...
    token: str
    folder_id: str


def yagpt_client_init(token, folder_id, timeout=60):
    return YagptClient(
        session=aiohttp.ClientSession(
            headers={
                'Authorization': f'Bearer {token}',
                'x-folder-id': folder_id
            },
            timeout=aiohttp.ClientTimeout(total=timeout)
        ),
        token=token,
        folder_id=folder_id
    )


async def yagpt_instruct(client, instruction, model='general', temperature=0, max_tokens=2000):
    response = await client.session.post(
        'https://llm.api.cloud.yandex.net/llm/v1alpha/instruct',
        json={
            'model': model,
            'generationOptions': {
                'partialResults': False,
                'temperature': temperature,
                'maxTokens': max_tokens,
            },
            'instructionText': instruction,
            'requestText': None
        }
    )
    response.raise_for_status()
    data = await response.json()

    #   {'result': {'alternatives': [{'text': 'На самом ...енно в своей форме.',
    #   'score': -2.3407514095306396,
    #   'num_tokens': '38'}],
    # 'num_prompt_tokens': '12'}}

    return data['result']['alternatives'][0]['text']


async def yagpt_singleturn(client, instruction, model='general', temperature=0, max_tokens=2000):
    response = await client.session.post(
        'https://llm.api.cloud.yandex.net/llm/v1alpha/chat',
        json={
            'model': model,
            'generationOptions': {
                'partialResults': False,
                'temperature': temperature,
                'maxTokens': max_tokens,
            },
            'messages': [],
            'instructionText': instruction,
        }
    )
    response.raise_for_status()
    data = await response.json()

    # {'result': {'message': {'role': 'Ассистент',
    #    'text': "Это высказывание о смертной казни ...к преступнику Жоржу Плотнику'у."},
    #   'num_tokens': '60'}}

    return data['result']['message']['text']


#######
#
#   WORKER
#
#####


# turbo gpt-3.5-turbo-0301
# turbo_2 gpt-3.5-turbo-0613
# gpt4 gpt-4-0314
# gpt4_2 gpt-4-0613

# gigachat v1.13.0

# yagpt_instruct v1alpha/instruct model=general
# yagpt_chat v1alpha/chat model=general
# yagpt_alisa ya.ru chat 2023-08

# saiga2_7b
# saiga2_13b


async def translate_worker(items):
    for item in items:
        try:
            item['answer'] = await openai_translate(item['instruction'])
        except openai.error.OpenAIError as error:
            print(repr(error), file=sys.stderr)


async def sbs_worker(items):
    for item in items:
        try:
            item['answer_ab'] = await openai_sbs(item['instruction'], item['answer_a'], item['answer_b'])
            item['answer_ba'] = await openai_sbs(item['instruction'], item['answer_b'], item['answer_a'])
        except openai.error.OpenAIError as error:
            print(repr(error), file=sys.stderr)

        else:
            item['result_ab'] = sbs_answer_result(item['answer_ab'])
            item['result_ba'] = sbs_answer_result(item['answer_ba'])
            item['result'] = sbs_agg_swap(item['result_ab'], item['result_ba'])


async def openai_infer_worker(items, model, request_timeout=60):
    for item in items:
        try:
            item['answer'] = await openai_singleturn(
                item['instruction'],
                model=model,
                request_timeout=request_timeout
            )
        except openai.error.OpenAIError as error:
            print(repr(error), file=sys.stderr)


async def gigachat_infer_worker(items, client):
    for item in items:
        try:
            item['answer'] = await gigachat_singleturn(client, item['instruction'])
        except (aiohttp.ClientError, AssertionError) as error:
            print(repr(error), file=sys.stderr)


class Limiter:
    # Ensure delay between sleep() calls >= min_delay

    def __init__(self, min_delay):
        self.min_delay = min_delay
        self.prev = 0

    async def sleep(self):
        while True:
            delay = time.monotonic() - self.prev
            if delay > self.min_delay:
                break

            await asyncio.sleep(self.min_delay - delay)

        self.prev = time.monotonic()


async def yagpt_infer_worker(client, limiter, items, mode='instruct'):
    assert mode in ('chat', 'instruct'), mode
    func = yagpt_instruct
    if mode == 'chat':
        func = yagpt_singleturn

    for item in items:
        await limiter.sleep()

        try:
            item['answer'] = await func(client, item['instruction'])
        except aiohttp.ClientError as error:
            print(repr(error), file=sys.stderr)

