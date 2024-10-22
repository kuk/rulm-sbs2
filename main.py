
import re
import sys
import uuid
import random
import json
import asyncio
import pickle
import html
import time
import statistics
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
import matplotlib.patches as mpatches

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
#   COSINE SIM
#
######


def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


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
        temperature=0,
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
    prompt = f'''Please act as an impartial judge and evaluate the quality of the responses provided by two AI assistants to the user question displayed below. You should choose the assistant that follows the user's instructions and answers the user's question better. Your evaluation should consider factors such as the helpfulness, relevance, accuracy, depth, creativity, and level of detail of their responses. Begin your evaluation by comparing the two responses and provide a short explanation. Avoid any position biases and ensure that the order in which the responses were presented does not influence your decision. Do not allow the length of the responses to influence your evaluation. Do not favor certain names of the assistants. Be as objective as possible. After providing your explanation, output two values on a scale of 1 to 10 indicating the scores for Assistant A and B, respectively. Output your final verdict by strictly following this format: [[{{Assistant A score}} {{Assistant B score}}]].

[User Question]
{instruction}

[The Start of Assistant A's Answer]
{answer_a}
[The End of Assistant A's Answer]

[The Start of Assistant B's Answer]
{answer_b}
[The End of Assistant B's Answer]
'''
    return await openai_singleturn(prompt, model='gpt-4-0613')


def sbs_name_models(answer, model_a, model_b):
    def repl1(match):
        value = match.group(1)
        if value == 'A':
            return model_a
        elif value == 'B':
            return model_b

    answer = re.sub(r'[A|a]ssistants? (A and B)', f'{model_a} and {model_b}', answer)
    answer = re.sub(r'[A|a]ssistant (A|B)', repl1, answer)

    def repl2(match):
        score_a, score_b = match.groups()
        return f'[[{model_a} - {score_a}, {model_b} - {score_b}]]'

    answer = re.sub(r'\[\[([\d\.]+)\s+([\d\.]+)\]\]', repl2, answer)
    return answer


def sbs_answer_scores(answer):
    a, b = None, None

    match = re.search(r'\[\[(\d+)(\.\d+)?\s+(\d+)(\.\d+)?\]\]', answer)
    if match:
        a, a_fraction, b, b_fraction = match.groups()
        if a_fraction:
            a = float(a + a_fraction)
        else:
            a = int(a)

        if b_fraction:
            b = float(b + b_fraction)
        else:
            b = int(b)

    return a, b


def sbs_scores_result(score_a, score_b):
    if score_a is None or score_b is None:
        return
    
    if score_a > score_b:
        return 'a'
    elif score_a < score_b:
        return 'b'
    else:
        return 'tie'


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


LABEL_TRANSLATE_CONFIG = '''
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


LABEL_CLASSIFY_CONFIG = '''
<View>
  <View style="display: grid; grid-template: auto/1fr 1fr">
    <Header value="instruction" />
    <Header value="category" />

    <Text name="instruction" value="$instruction" />

    <Choices name="category" toName="instruction" choice="single" showInline="true">
      <Choice value="bad" />

      <Choice value="brainstorm" />
      <Choice value="reason" />
      <Choice value="qa" />
      <Choice value="closed qa" />
      <Choice value="explain" />

      <Choice value="writing" />
      <Choice value="roleplay" />
      <Choice value="joke" />
      <Choice value="poem" />
      <Choice value="cooking" />

      <Choice value="outline" />
      <Choice value="plan" />
      <Choice value="invent" />
      <Choice value="advice" />
      <Choice value="instruction" />

      <Choice value="grammar" />
      <Choice value="translate" />

      <Choice value="coding" />
      <Choice value="summary" />
      <Choice value="enumerate" />

      <Choice value="chat" />
      <Choice value="extract" />
      <Choice value="math" />
    </Choices>
  </View>

  <View>
    <Text name="answers" value="$answers" />
  </View>
</View>
'''


def classify_label_item(item, model_answers):
    models = sorted(model_answers, key=lambda _: len(model_answers[_]))
    parts = []
    for model in models:
        answer = model_answers[model]
        parts.append(f'''# {model}
{answer}''')
    answers = '\n\n'.join(parts)

    label_item = {
        'data': {
            'id': item['id'],
            'instruction': item['instruction'],
            'answers': answers,
            'max_sim': item['max_sim'],
            'category': item['category'],
        }
    }
    if item['category']:
        label_item['predictions'] = [{
            'result': [{
                'from_name': 'category',
                'to_name': 'instruction',
                'type': 'choices',
                'value': {
                    'choices': [item['category']]
                }
            }]
        }]
    return label_item


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


LABEL_SBS_CONFIG = '''
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
      <Choice value="a"/>
      <Choice value="b"/>
      <Choice value="tie"/>
   </Choices>

   <Text name="answer" value="$answer" />
  </View>
</View>
'''


def sbs_label_item(item):
    if not item['swap']:
        answer = sbs_name_models(item['answer'], item['model_a'], item['model_b'])
    else:
        answer = sbs_name_models(item['answer'], item['model_b'], item['model_a'])

    return {
        'data': {
            'id': item['id'],
            'model_a': item['model_a'],
            'model_b': item['model_b'],
            'instruction': item['instruction'],
            'answer_a': item['answer_a'],
            'answer_b': item['answer_b'],
            'answer': answer,
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


async def gigachat_request(client, prompt, session_id, model_type='GigaChat:v1.2.17.0'):
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


class YagptError(Exception):
    pass


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


async def yagpt_tokenize(client, text, model='general'):
    response = await client.session.post(
        'https://llm.api.cloud.yandex.net/llm/v1alpha/tokenize',
        json={
            'model': model,
            'text': text
        }
    )
    if response.status != 200:
        raise YagptError(await response.text())

    # {'tokens': [{'id': '0', 'text': '<s>', 'special': True},
    #  {'id': '838', 'text': '▁У', 'special': False},
    #  {'id': '1375', 'text': '▁меня', 'special': False},

    data = await response.json()
    return [_['text'] for _ in data['tokens']]


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
    if response.status != 200:
        raise YagptError(await response.text())

    #   {'result': {'alternatives': [{'text': 'На самом ...енно в своей форме.',
    #   'score': -2.3407514095306396,
    #   'num_tokens': '38'}],
    # 'num_prompt_tokens': '12'}}

    data = await response.json()
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
    if response.status != 200:
        raise YagptError(await response.text())

    # {'result': {'message': {'role': 'Ассистент',
    #    'text': "Это высказывание о смертной казни ...к преступнику Жоржу Плотнику'у."},
    #   'num_tokens': '60'}}

    data = await response.json()
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
# gigachat_2 v1.2.17.0

# yagpt_instruct v1alpha/instruct model=general
# yagpt2_instruct v1alpha/instruct model=general "потом еще добавим нейминнг на yagpt-2.0"
# yagpt2_instruct_2 "нормальную на большую модель (которой Алиса пользуется"
# yagpt_chat v1alpha/chat model=general
# yagpt_alisa ya.ru chat 2023-08

# saiga2_7b
# saiga2_13b

# vicuna_13b lmsys/vicuna-13b-v1.5


async def translate_worker(items):
    for item in items:
        try:
            item['answer'] = await openai_translate(item['instruction'])
        except openai.error.OpenAIError as error:
            print(repr(error), file=sys.stderr)


async def sbs_worker(items):
    for item in items:
        swap = False
        answer_a, answer_b = item['answer_a'], item['answer_b']
        if random.random() < 0.5:
            swap = True
            answer_a, answer_b = answer_b, answer_a

        try:
            answer = await openai_sbs(item['instruction'], answer_a, answer_b)
        except openai.error.OpenAIError as error:
            print(repr(error), file=sys.stderr)

        else:
            score_a, score_b = sbs_answer_scores(answer)
            if swap:
                score_a, score_b = score_b, score_a

            item['swap'] = swap
            item['answer'] = answer
            item['score_a'] = score_a
            item['score_b'] = score_b
            item['result'] = sbs_scores_result(score_a, score_b)


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


async def gigachat_infer_worker(client, items):
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


async def yagpt_infer_worker(client, limiter, items, mode='instruct', model='general'):
    assert mode in ('chat', 'instruct'), mode
    func = yagpt_instruct
    if mode == 'chat':
        func = yagpt_singleturn

    for item in items:
        await limiter.sleep()

        try:
            item['answer'] = await func(client, item['instruction'], model=model)
        except YagptError as error:
            print(repr(error), file=sys.stderr)


#######
#
#  CENSOR
#
#####


CENSOR_SUBSTRINGS = [
    'Что-то в вашем вопросе меня смущает',
    'Может, поговорим на другую тему?',
    'я совсем не хочу говорить на эту тему',
    'такие темы я не обсуждаю, чтобы никому не было обидно или неприятно',
    'Не люблю менять тему разговора, но вот сейчас тот самый случай',
    'говорить на эту тему я совсем не готова, чтобы никого не обидеть',
]


def is_censor(answer):
    for substring in CENSOR_SUBSTRINGS:
        if substring in answer:
            return True
