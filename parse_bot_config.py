#!/usr/bin/env python3

import csv

# Датасет botconfig
fname = 'botconfig.csv'
with open(fname, encoding='utf-8', newline='') as f:
    reader = csv.DictReader(f)
    print(reader.fieldnames)
    lines = list(reader)

codes = [line['Ячейка с BOT_CONFIG'] for line in lines]
print(len(codes))

# Отбрасывание кода, который не идет после фразы botconfig и идет после def включительно
config_codes = []

for code in codes:
    if 'BOT_CONFIG =' in code:
        code = code.split('BOT_CONFIG =')[1]
    if 'bot_config =' in code:
        code = code.split('bot_config =')[1]
    if 'BOT_CONFIG=' in code:
        code = code.split('BOT_CONFIG=')[1]
    if 'BOT_CONFIG  =' in code:
        code = code.split('BOT_CONFIG  =')[1]
    if 'def ' in code:
        code = code.split('\ndef ')[0]

    code = code.strip()  # отбрасывание пробелов и переносы строк слева/справа

    config_codes.append(code)

print(len(config_codes))

# Проверка botconfig на питоновский код
configs = []
errors = 0
for code in config_codes:
    try:
        configs.append(eval(code))
    except Exception as e:
        print(code)
        print('-' * 30)
        print(e)
        print('-' * 100)
        errors += 1

# Количество ошибок и конфигов
print(f'{errors} errors ({errors / len(config_codes) * 100:.2f}%)')
print(len(configs), 'configs')

# Слияние в один большой конфиг
big_config = {
    'intents': {},
    'failure_phrases': []
}

for config in configs:
    if isinstance(config, dict):
        if 'intents' in config:
            for intent, value in config['intents'].items():
                if intent not in big_config['intents']:
                    big_config['intents'][intent] = {
                        'examples': [],
                        'responses': []
                    }
                if isinstance(value, dict):
                    big_config['intents'][intent]['examples'] += value.get('examples', [])
                    big_config['intents'][intent]['responses'] += value.get('responses', [])
        big_config['failure_phrases'] += config.get('failure_phrases', [])

# Чистка intents от повторов и мусора
for intent, value in big_config['intents'].items():
    value['examples'] = list(set(value['examples']))
    value['responses'] = list(set(value['responses']))
    value['examples'] = [s.strip() for s in value['examples'] if isinstance(s, str) and s.strip()]
    value['responses'] = [s.strip() for s in value['responses'] if isinstance(s, str) and s.strip()]

big_config['failure_phrases'] = list(set(big_config['failure_phrases']))
big_config['failure_phrases'] = [s.strip() for s in big_config['failure_phrases'] if isinstance(s, str) and s.strip()]

# Намерений
print(len(big_config['intents']))

# Примеров
print(sum(len(intent_data['examples']) for intent_data in big_config['intents'].values()))

# Ответов
print(sum(len(intent_data['responses']) for intent_data in big_config['intents'].values()))

# Заглушек
print(len(big_config['failure_phrases']))

print(big_config)
