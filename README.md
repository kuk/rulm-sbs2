# rulm-sbs2

Бенчмарк сравнивает русские аналоги ChatGPT: Saiga, YandexGPT, Gigachat. Принцип работы бенчмарка похож на <a href="https://github.com/tatsu-lab/alpaca_eval">AlpacaEval</a> и <a href="https://huggingface.co/spaces/lmsys/chatbot-arena-leaderboard">MT-Bench</a>: бенчмарк собирает ответы моделей на <a href="data/tasks.md">500 заданий из 15+ категорий</a>, использует GPT4, чтобы сравнить качество ответов. <a href="#internal">Подробнее про внутреннее устройство бенчмарка</a>.

> (!) На других заданиях могут быть другие результаты. Читать <a href="data/tasks.md">примеры заданий</a> и <a href="#tasks">почему они именно такие</a>.

> (!) Ответы оценивает GPT4, а не живой человек, в ~15% случаев GPT4 ошибается. Читать <a href="data/sbs.md">примеры оценок GPT4</a> и <a href="#gpt_judge">почему выбрали GPT4 вместо Толоки<a>.

<br/>

- gpt4_2 — <a href="https://platform.openai.com/docs/models/gpt-4">gpt-4-0613</a>, turbo_2 — <a href="https://platform.openai.com/docs/models/gpt-3-5">gpt-3.5-turbo-0613</a>, saiga2_* — <a href="https://huggingface.co/collections/IlyaGusev/saiga2-lora-6505d4ccc3d1e53166b636cd">IlyaGusev/saiga2-lora</a>, vicuna_13b — <a href="https://huggingface.co/lmsys/vicuna-13b-v1.5">lmsys/vicuna-13b-v1.5</a>, yagpt_instruct — <a href="https://cloud.yandex.ru/docs/yandexgpt/api-ref/TextGeneration/instruct">Cloud YandexGPT API </a>, gigachat — неофициальное API v1.13.
- Все модели сравниваем с turbo_2, поэтому точка turbo_2 в нуле. Подробнее как бенчмарк считает "Баллы B - баллы A" в <a href="#internal">разделе про внутреннее устройство</a>.
- gpt4_2 чуть лучше turbo_2, задания недостаточно сложные, чтобы разделить эти модели.
- gigachat и yagpt_instruct на уровне saiga2_7b и saiga2_13b соответственно. <a href="https://ya.ru/gpt/2">YandexGPT 2</a> пока нет в бенчмарке.
- vicuna_13b на уровне saiga2_13b, хотя в обучении Vicuna не было акцента на русский.
- Топовые решения для русского — модель Openai. saiga2_70b приближается, но ее тяжело инференсить.
<img width="689" alt="image" src="https://github.com/kuk/rulm-sbs2/assets/153776/8f0b7e1b-f9ab-46dd-8bb4-95c6a7f586c1">

<br/>
<br/>
<br/>

Результаты gigachat, yagpt_instruct и saiga2_13b по категориям:
- <a href="data/tasks.md#writing">writing</a> — "напиши пост в блог о ...", "напиши письмо начальнику"; <a href="data/tasks.md#brainstorm">brainstorm</a> — накидать идей "как ИИ мог бы быть полезен в медицине", "что если бы Эйнштейн занимался биологией"; <a href="data/tasks.md">примеры заданий по остальным категориям</a>.
- Все модели сравниваем с turbo_2, поэтому диаграмма turbo_2 проходит через 0.
- gpt4_2 заметно лучше turbo_2 только на <a href="data/tasks.md#reason">reason</a>, задания типа "сколько снежинок выпадает за зиму", в остальных категориях задания не достаточно сложных, чтобы разделить эти модели.
- gigachat заметно хуже yagpt_instruct на math и coding.
- У saiga2_13b похожая диаграмма на yagpt_instruct, получше только <a href="data/tasks.md#extract">extract</a> — задания типа "извлеки адрес недвижимости", "к какой категории относится письмо", "оформи в виде таблицы".
<img width="686" alt="image" src="https://github.com/kuk/rulm-sbs2/assets/153776/78e9fe9d-62e6-43a7-9394-f41020f8bc03">

<br/>
<br/>
<br/>

Результаты saiga2_* по категориям:
- У saiga2_* и vicuna_13b похожие диаграммы по категориям, у всех базовая модель Llama 2. Базовая модель важнее, чем файнтюн на инструкциях.
- Для saiga2_70b пока мало ответов, большая вариация. 
<img width="669" alt="image" src="https://github.com/kuk/rulm-sbs2/assets/153776/d35f4e85-584b-487f-9d9a-58ca33b6402f">


<a name="internal"></a>
## Принцип работы

Рассмотрим одно из заданий, сравним ответы turbo_2 и gigachat на него:
<table>
<tr><td colspan="2">
#coding
<br/>
Напиши функцию на Python которая находит самую длинную общую подпоследовательность двух строк с помощью динамического программирования.
</td></tr>
<tr><td>turbo_2</td><td>gigachat</td></tr>
<tr>
<td valign="top" width="50%">
Вот реализация функции, которая находит самую длинную общую подпоследовательность двух строк с помощью динамического программирования:<br/>
<br/>
```python<br/>
def longest_common_subsequence(str1, str2):<br/>
    m = len(str1)<br/>
    n = len(str2)<br/>
    # Создаем таблицу для хранения длин подпоследовательностей<br/>
    lcs_table = [[0] * (n + 1) for _ in range(m + 1)]<br/>
<br/>
    # Заполняем таблицу поочередно сравнивая символы строк<br/>
    for i in range(1, m + 1):<br/>
        for j in range(1, n + 1):<br/>
            if str1[i - 1] == str2[j - 1]:<br/>
                lcs_table[i][j] = lcs_table[i - 1][j - 1] + 1<br/>
            else:<br/>
                lcs_table[i][j] = max(lcs_table[i - 1][j], lcs_table[i][j - 1])<br/>
    <br/>
    # Восстанавливаем самую длинную общую подпоследовательность<br/>
    lcs = []<br/>
    i = m<br/>
    j = n<br/>
    while i &gt; 0 and j &gt; 0:<br/>
        if str1[i - 1] == str2[j - 1]:<br/>
            lcs.append(str1[i - 1])<br/>
            i -= 1<br/>
            j -= 1<br/>
        elif lcs_table[i - 1][j] &gt; lcs_table[i][j - 1]:<br/>
            i -= 1<br/>
        else:<br/>
            j -= 1<br/>
<br/>
    # Возвращаем обратное отображение списка, чтобы получить подпоследовательность в правильном порядке<br/>
    return &#x27;&#x27;.join(lcs[::-1])<br/>
```<br/>
<br/>
Пример использования:<br/>
<br/>
```python<br/>
str1 = &quot;ABCDGH&quot;<br/>
str2 = &quot;AEDFHR&quot;<br/>
result = longest_common_subsequence(str1, str2)<br/>
print(result)  # Выведет &quot;ADH&quot;<br/>
```<br/>
<br/>
В данном примере функция `longest_common_subsequence` найдет самую длинную общую подпоследовательность между строками &quot;ABCDGH&quot; и &quot;AEDFHR&quot;, которая равна &quot;ADH&quot;.
</td>

<td valign="top" width="50%">
Конечно, вот пример функции на Python, которая находит самую длинную общую подпоследовательность двух строк с помощью динамического программирования:<br/>
<br/>
&lt;code&gt;{python}def longest_common_subsequence(str1, str2):<br/>
    n = len(str1)<br/>
    m = len(str2)<br/>
    dp = [[0] * (m + 1) for _ in range(n + 1)]<br/>
    <br/>
    # Заполняем первую строку и первый столбец нулями<br/>
    for i in range(1, m + 1):<br/>
        dp[i][0] = 0<br/>
    <br/>
    # Заполняем оставшиеся ячейки массива<br/>
    for j in range(1, n + 1):<br/>
        if str1[j - 1] == str2[j]:<br/>
            dp[j][1] = dp[j - 1][1] + 1<br/>
        else:<br/>
            dp[j][1] = max(dp[j - 1][1], dp[j][1])<br/>
    <br/>
    # Находим максимальное значение в массиве и возвращаем его<br/>
    return dp[n][m]<br/>
&lt;/code&gt;<br/>
<br/>
Функция принимает две строки `str1` и `str2` и возвращает длину самой длинной общей подпоследовательности этих строк. Для этого мы используем двумерный массив `dp`, где каждый элемент представляет собой индекс начала подпоследовательности для первой строки и соответствующий индекс начала подпоследовательности для второй строки. Мы заполняем первую строку и первый столбец нулями, чтобы начать поиск с первого символа каждой строки. Затем мы заполняем оставшиеся ячейки массива, используя алгоритм динамического программирования. В конце мы находим максимальное значение в массиве и возвращаем его.
</td>
<tr>
<table>

Используем чуть модифицированный промпт из <a href="https://arxiv.org/abs/2306.05685">Judging LLM-as-a-judge with MT-Bench and Chatbot Arena</a>. GPT4 <a href="https://huggingface.co/blog/llm-leaderboard">больше нравится ответ, который идет первым</a>. Случайно меняем ответы места, чтобы не было перекоса. В ответе ниже "Assistant A" и "Assistant B" заменены на названия моделей:
<table>
  <tr>
    <td>
Please act as an impartial judge and evaluate the quality of the responses provided by two AI assistants to the user question displayed below. You should choose the assistant that follows the user&#x27;s instructions and answers the user&#x27;s question better. Your evaluation should consider factors such as the helpfulness, relevance, accuracy, depth, creativity, and level of detail of their responses. Begin your evaluation by comparing the two responses and provide a short explanation. Avoid any position biases and ensure that the order in which the responses were presented does not influence your decision. Do not allow the length of the responses to influence your evaluation. Do not favor certain names of the assistants. Be as objective as possible. After providing your explanation, output two values on a scale of 1 to 10 indicating the scores for Assistant A and B, respectively. Output your final verdict by strictly following this format: [[{Assistant A score} {Assistant B score}]].<br/>
<br/>
[User Question]<br/>
{instruction}<br/>
<br/>
[The Start of Assistant A&#x27;s Answer]<br/>
{answer_a}<br/>
[The End of Assistant A&#x27;s Answer]<br/>
<br/>
[The Start of Assistant B&#x27;s Answer]<br/>
{answer_b}<br/>
[The End of Assistant B&#x27;s Answer]
</td></tr>
<tr><td>
gigachat provided a Python function for finding the longest common subsequence of two strings using dynamic programming. However, the function seems to have a mistake in the loop where it compares characters from the two strings. It seems to be comparing characters from the same string instead of comparing characters from the two different strings. Also, the function only returns the length of the longest common subsequence, not the subsequence itself.<br/>
<br/>
turbo_2 also provided a Python function for the same task. This function appears to be correct, as it properly compares characters from the two strings and builds up the longest common subsequence in a dynamic programming table. Additionally, this function also reconstructs the longest common subsequence from the dynamic programming table and returns it, which is more in line with the user&#x27;s question. turbo_2 also provided an example of how to use the function.<br/>
<br/>
Therefore, turbo_2&#x27;s response is more accurate, helpful, and detailed than gigachat&#x27;s response.<br/>
<br/>
[[gigachat - 5, turbo_2 - 10]]
</td></tr>
</table>

GPT4 неправильно назвал проблему "gigachat seems to be comparing characters from the same string instead of comparing characters from the two different strings", gigachat сравнивает символы из разных строк, но по неверным индексам "str1[j - 1] == str2[j]". GPT4 правильно заметил "function only returns the length of the longest common subsequence", действительно, по заданию нужно вернуть общую подпоследовательность, а не ее длину. Дельта между turbo_2 и gigachat на этом задании 10 - 5 = 5 баллов.

Повторяем процедуру для всех заданий, для всех моделей:
- Пример про общую подпоследовательность попадает в строку "gigachat", в оранжевый сектор "<= -3".
- Для saiga2_* пока посчитали не все задания.
<img width="751" alt="image" src="https://github.com/kuk/rulm-sbs2/assets/153776/f3875521-e5fb-43fb-ba49-d532727f82e0">

Складывам дельты, делим на число заданий, для gigachat получаем ~-3.5. Доверительный интервал [0.5, 0.95] считаем бутстрэпом, у saiga2_* меньше ответов, шире доверительные интревалы.

<img width="689" alt="image" src="https://github.com/kuk/rulm-sbs2/assets/153776/8f0b7e1b-f9ab-46dd-8bb4-95c6a7f586c1">

<a href="data/tasks.md">Больше примеров заданий</a>, <a href="data/sbs.md">больше ответов моделей и оценок GPT4</a>.

<a name="gpt_judge"></a>
## GPT4 vs Толока

В проекте Saiga все модели оценивают толокеры, оценки собраны в <a href="https://huggingface.co/datasets/IlyaGusev/rulm_human_preferences">IlyaGusev/rulm_human_preferences</a>. Возьмем 100 случайных пар ответов из датасета, повторим оценку используя GPT4. 70 из 100 оценок совпадают, остальные 30 проверим вручную, 15 из 30 — скорее правы толокеры, остальные 15 — скорее права GPT4.

<table>
<tr>
    <td width="50%"><b>Толока</b></td>
    <td><b>GPT4</b></td>
</tr>
<tr valign="top">
    <td>Цена — 67$ за 1000 заданий с перекрытием 5</td>
    <td>45$ за 1000 заданий</td>
</tr>
<tr valign="top">
    <td>Скорость — 1 час модерация проекта + ~250 заданий в час</td>
    <td>~1 задание в секунду</td>
</tr>
<tr valign="top">
    <td>Толокеры ошибаются в ~15% заданий, им сложно оценить задания про программирование, математику</td>
    <td>~15% заданий ошибается. Не может оценить задания, где у самой GPT4 низкое качество: задания на знание русского языка, задания на запретные темы</td>
</tr>
<tr valign="top">
    <td>Бинарная оценка: А лучше/хуже B. Уверенность можно оценивать через перекрытие: 3 толока сказали лучше, 2 — хуже.</td>
    <td>Оценивает в баллах на сколько A лучше/хуже B</td>
</tr>
<tr valign="top">
    <td>Толокеры беспристрастны</td>
    <td>GPT4 скорее нравятся ответы GPT4 и Turbo</td>
</tr>
<tr valign="top">
    <td>Толокеры не объясняют решение</td>
    <td>Объясняет решение</td>
</tr>
</table>

<a name="tasks"></a>
## Почему именно такие задания

Для английского есть готовые открытые датасеты с заданиями:
- <a href="https://github.com/yizhongw/self-instruct/blob/main/human_eval/user_oriented_instructions.jsonl">Alpaca</a> — 250 заданий, тестсет Alpaca.
- <a href="https://github.com/lm-sys/vicuna-blog-eval/blob/main/eval/table/question.jsonl">Vicuna</a> — 80 заданий, тестсет Vicuna.
- <a href="https://huggingface.co/datasets/HuggingFaceH4/mt_bench_prompts">Vicuna 2</a> — новые 80 заданий из <a href="https://lmsys.org/blog/2023-06-22-leaderboard/">MT-Bench</a>.
- <a href="https://huggingface.co/datasets/lmsys/chatbot_arena_conversations">Arena</a> — логи <a href="https://lmsys.org/blog/2023-05-03-arena/">Chatbot Arena</a>
- <a href="https://huggingface.co/datasets/theblackcat102/sharegpt-english">ShareGPT</a> — дамп <a href="http://sharegpt.com">sharegpt.com</a>.
- <a href="https://github.com/arnav-gudibande/koala-test-set/blob/main/koala_test_set.jsonl">Koala</a> — тестсет <a href="https://bair.berkeley.edu/blog/2023/04/03/koala/">Koala</a>.
- <a href="https://huggingface.co/datasets/Anthropic/hh-rlhf">HH</a>
- <a href="https://huggingface.co/datasets/OpenAssistant/oasst1">Open Assistant</a>
- <a href="https://huggingface.co/datasets/databricks/databricks-dolly-15k">Dolly</a>

<a href="data/tasks.md">500 заданий из этого бенчмарка</a> = переведенные на русский Alpaca + Vicuna + часть Arena. 

В ShareGPT попадают задания, где ChatGPT хорошо сработала, сравниваться на них с ChatGPT нечестно. Плюс англоязычные модели типа Vicuna учились на ShareGPT.

Open Assistant — тоже риск, что задания есть в трейне англоязычных моделей.

HH, Dolly — однообразные синтетические задания.

Vicuna 2, Koala — может быть добавим в будущем.

## Другие бенчмарки для русскоязычных LLM

- <a href="https://russiansuperglue.com">russiansuperglue.com</a>
- <a href="https://github.com/NLP-Core-Team/mmlu_ru">Перевод MMLU на русский</a>
- <a href="http://tape-benchmark.com">tape-benchmark.com</a>
- <a href="https://habr.com/ru/companies/sberdevices/articles/761120/">GigaChat против всех — тестируем языковую модель на генеративных задачах</a>

## Разработка

```bash
python -m venv ~/.venvs/rulm-sbs2
source ~/.venvs/rulm-sbs2/bin/activate

pip install \
  tqdm \
  pandas pyarrow \
  matplotlib \
  aiohttp \
  openai \
  label-studio-sdk

pip install ipywidgets ipykernel
python -m ipykernel install --user --name rulm-sbs2
```
