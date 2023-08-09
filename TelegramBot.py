#!/usr/bin/env python3

import random
import nltk
from bot_config import config
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext


# Подготовка датасета
# Конфиг
BOT_CONFIG = config

# Intent classifier
texts = []
intent_names = []

for intent, intent_data in BOT_CONFIG['intents'].items():
    for example in intent_data['examples']:
        texts.append(example)
        intent_names.append(intent)

# print(len(texts))

# # Векторизация
# vectorizer = CountVectorizer()
# X = vectorizer.fit_transform(texts)

# print(len(vectorizer.get_feature_names()))  # количество векторов
# print(vectorizer.get_feature_names())  # упорядочные элементы словаря
# print(list(X.toarray()[0]))

# vectorizer.transform(['Привет'])[0].toarray()

# # Классификация
# clf = LogisticRegression()
# # Обучение классификатора
# clf.fit(X, intent_names)  # список векторов и список наименований намерений, которые соответствуют этим векторам
# # Предсказание, к кому классу принадлежит вектор
# predict = clf.predict(vectorizer.transform(['Привет', 'сколько тебе лет?', 'как тебя зовут?', 'klsckjln al ascm lcs']))
# # Вектор вероятности того, что данный пример соответствует к какому-либо из классов
# proba = clf.predict_proba(vectorizer.transform(['фы вф вфы выфвфы']))

# print(predict)
# print(proba)

# Оценка качества
# scores = []

vectorizer = TfidfVectorizer(ngram_range=(2, 4), analyzer='char')
X = vectorizer.fit_transform(texts)
clf = LinearSVC()
clf.fit(X, intent_names)


# for i in range(10):
#     # Выборка обучающая и тестовая
#     X_train, X_test, y_train, y_test = train_test_split(X, intent_names)
#
#     clf = LinearSVC()
#     clf.fit(X_train, y_train)
#
#     score = clf.score(X_test, y_test)
#     print(score)
#     scores.append(score)
#
# print('Average:', sum(scores) / len(scores))
#
# clf = LinearSVC()
# clf.fit(X, intent_names)
# clf.score(X, intent_names)


def clear_text(text):
    text = text.lower()
    text = ''.join(char for char in text if char in 'абвгдеёжзиклмнопрстуфхчшщъыьэюя -')
    return text


def classify_intent(replica):
    intent = clf.predict(vectorizer.transform([replica]))[0]

    examples = BOT_CONFIG['intents'][intent]['examples']
    for example in examples:
        example = clear_text(example)
        if len(example) > 0:
            if abs(len(example) - len(replica)) / len(example) < 0.5:
                distance = nltk.edit_distance(replica, example)
                if len(example) and distance / len(example) < 0.5:
                    return intent


def get_answer_by_intent(intent):
    if intent in BOT_CONFIG['intents']:
        responses = random.choice(BOT_CONFIG['intents'][intent]['responses'])
        return responses


# Generative model
with open('dialogues.txt', encoding='utf-8', newline='') as dialogues_file:
    dialogues_text = dialogues_file.read()

dialogues = dialogues_text.split('\n\n')

dataset = []  # [[question, answer], ...]
questions = set()

for dialogue in dialogues:
    replicas = dialogue.split('\n')
    replicas = replicas[:2]

    if len(replicas) == 2:
        question, answer = replicas
        question = clear_text(question[2:])
        answer = answer[2:]

        if len(question) > 0 and question not in questions:
            questions.add(question)
            dataset.append([question, answer])

dataset_by_word = {}  # {word: [[question with word, answer], ...], ...}

for question, answer in dataset:
    words = question.split(' ')
    for word in words:
        if word not in dataset_by_word:
            dataset_by_word[word] = []
        dataset_by_word[word].append([question, answer])

dataset_by_word_filtered = {}
for word, word_dataset in dataset_by_word.items():
    word_dataset.sort(key=lambda pair: len(pair[0]))
    dataset_by_word_filtered[word] = word_dataset[:1000]


def generate_answer(replica):
    def generate_answer(replica):
        replica = clear_text(replica)
        if not replica:
            return

        words = set(replica.split(' '))
        words_dataset = []

        for word in words:
            if word in dataset_by_word_filtered:
                word_dataset = dataset_by_word_filtered[word]
                words_dataset += word_dataset

        results = []  # [[question, answer, distance], ...]
        for question, answer in dataset:
            if abs(len(question) - len(replica)) / len(question) < 0.2:
                distance = nltk.edit_distance(replica, question)
                if distance / len(question) < 0.2:
                    results.append([question, answer, distance])

        question, answer, distance = min(results, key=lambda three: three[2])
        return answer


# Stubs
def get_stub():
    failure_phrases = random.choice(BOT_CONFIG['failure_phrases'])
    return failure_phrases


# Bot logig
stats = {'intents': 0, 'generative': 0, 'stubs': 0}


def bot(replica):
    # NLU
    intent = classify_intent(replica)

    # Получение ответа

    # Правила
    if intent:
        answer = get_answer_by_intent(intent)
        if answer:
            stats['intents'] += 1
            return answer

    # Генеративная модель
    answer = generate_answer(replica)
    if answer:
        stats['generative'] += 1
        return answer

    # Заглушка
    answer = get_stub()
    stats['stubs'] += 1
    return answer


print(bot('Сколько тебе лет?'))

# Telegram bot
def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi!')


def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    update.message.reply_text('Help!')


def run_bot(update: Update, context: CallbackContext) -> None:
    response = bot(update.message.text)
    update.message.reply_text(response)
    print(update.message.text)
    print(response)
    print(stats)
    print()


def main():
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater("1533499801:AAGx4dJej7SU6W5CQg9u8X0z-RK3FrwFKJ0")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, run_bot))

    # Start the Bot
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
