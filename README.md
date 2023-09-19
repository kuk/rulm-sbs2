# rulm-sbs2

Бенчмарк сравнивание русские аналоги ChatGpt: Saiga, YandexGpt, Gigachat. Принцип работы похож на <a href="https://github.com/tatsu-lab/alpaca_eval">AlpacaEval</a>, бенчмарк собирает ответы моделей на <a href="data/task.md">500 заданий из 15 категорий</a>, использует GPT4, чтобы сравнить качество ответов. Подробнее про <a href="#internal">внутреннее устройство бенчмарка</a>.

> (!) Делаем выводы по 500 ответам. На других заданиях могут быть другие результы. <a href="data/tasks.md">Читать задания</a>. Подробнее <a href="#qa_tasks">почему именно такие задания</a>.

> (!) Ответы оценивает GPT4, а не живой человек, ~15% случаев модель ошибается. <a href="data/sbs.md">Читать оценки GPT4</a>. Подробнее <a href="#gpt_judge">почему GPT4, плюсы и минусы<a>.

- gpt4_2 — <a href="https://platform.openai.com/docs/models/gpt-4">gpt-4-0613</a>, turbo_2 — <a href="https://platform.openai.com/docs/models/gpt-3-5">gpt-3.5-turbo-0613</a>, saiga2_* — <a href="https://huggingface.co/collections/IlyaGusev/saiga2-lora-6505d4ccc3d1e53166b636cd">IlyaGusev/saiga2-lora</a>, vicuna_13b — <a href="https://huggingface.co/lmsys/vicuna-13b-v1.5">lmsys/vicuna-13b-v1.5</a>, yagpt_instruct — <a href="https://cloud.yandex.ru/docs/yandexgpt/api-ref/TextGeneration/instruct">Cloud YandexGPT API </a>, gigachat — неофициальное API v1.13.
- gigachat и yagpt_instruct на уровне saiga2_7b и saiga2_13b соответственно. <a href="https://ya.ru/gpt/2">YandexGPT2</a> пока нет в бенчмарке.
- vicuna_13b на уровне saiga2_13b, хотя в обучении не было акцента на русский.
- gpt4_2 чуть лучше turbo_2, задания недостаточно сложные, чтобы разделить модели.
<img width="689" alt="image" src="https://github.com/kuk/rulm-sbs2/assets/153776/8f0b7e1b-f9ab-46dd-8bb4-95c6a7f586c1">


- <a href="data/tasks.md">Примеры заданий по категориям</a>, например, <a href="data/tasks.md#extract">extract</a> — извлечь структурированную инфу из текста "дан твит, является ли он оскорбительным или нет", "оформите следующие данные в виде таблицы ...", "Извлеките адрес недвижимости ...".
<img width="873" alt="image" src="https://github.com/kuk/rulm-sbs2/assets/153776/91659e5f-b195-4041-ad3b-8fe1bc7e397d">

<a name="internal"></a>
## Принцип работы

Рассмотрим одно из заданий, сравним ответы Turbo и Gigachat на него:
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

Используем промпт из <a href="https://arxiv.org/abs/2306.05685">Judging LLM-as-a-judge with MT-Bench and Chatbot Arena</a>, просим GPT4 сравнить ответы:<table>
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

GPT4 неправильно назвал проблему "gigachat seems to be comparing characters from the same string instead of comparing characters from the two different strings", Gigachat сравнивает символы из разных строк, но по неверным индексам "str1[j - 1] == str2[j]". GPT4 правильно заметил "function only returns the length of the longest common subsequence", действительно, по заданию нужно вернуть общую подпоследовательность, а не ее длину. Дельта между Turbo и Gigachat на этом задании 10 - 5 = 5 баллов.

Повторяем процедуру для всех заданий, для всех моделей:

- Пример про общую подпоследовательность попадает в строку "gigachat", в оранжевый сектор "<= -3".
- Для saiga2_* пока посчитали не все задания.

<img width="751" alt="image" src="https://github.com/kuk/rulm-sbs2/assets/153776/f3875521-e5fb-43fb-ba49-d532727f82e0">

Складывам дельты, делим на число заданий, для saiga2_7b, например, получается ~-2. Доверительный интервал [0.5, 0.95] получаем бутстрэппингом:
<img width="689" alt="image" src="https://github.com/kuk/rulm-sbs2/assets/153776/8f0b7e1b-f9ab-46dd-8bb4-95c6a7f586c1">

<a href="data/tasks.md">Больше примеров заданий</a>, все задания в <a href="data/tasks.json">tasks.json</a>, больше ответов моделей и оценок GPT4 <a href="data/sbs.md">

## Похожие бенчмарки

https://russiansuperglue.com
http://tape-benchmark.com
https://github.com/NLP-Core-Team/mmlu_ru
https://habr.com/ru/companies/sberdevices/articles/761120/

<a name="gpt_judge"></a>
## GPT4 vs Толока

## Ссылочки по теме

## Вопросы и ответы


<a name="qa_tasks"></a>
### Почему именно такие задания?

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
