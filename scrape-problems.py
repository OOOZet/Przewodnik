#!/usr/bin/env -S /bin/sh -c 'exec "$(dirname "$0")/venv/bin/python3" "$0" "$@"'

import csv, re, requests
from bs4 import BeautifulSoup

def to_roman_numeral(num):
  units = [
    ( 'I', 1),
    ('IV', 4),
    ( 'V', 5),
    ('IX', 9),
    ( 'X', 10),
    ('XL', 40),
    ( 'L', 50),
    ('XC', 90),
    ( 'C', 100),
    ('CD', 400),
    ( 'D', 500),
    ('CM', 900),
    ( 'M', 1000),
  ]
  string = ''
  for symbol, value in reversed(units):
    while num >= value:
      num -= value
      string += symbol
  return string

problems = []

problemset_url = 'https://oi.edu.pl/l/oi_zadania/'
response = requests.get(problemset_url)
response.raise_for_status()
html = BeautifulSoup(response.content, 'lxml')

for contest in html.find_all(class_='contest'):
  url = f'{problemset_url}#{contest["id"]}'
  olympiad = int(contest['id'].removeprefix('oi-'))
  competition = f'{to_roman_numeral(olympiad)} OI'

  for row in contest.find('tbody').find_all('tr'):
    cols = row.find_all('td')

    codes = []
    for a in row.find_all('a'):
      if 'Trudniejsza wersja' in a.text:
        continue
      for pattern in [r'\boi/\d+/(\w+)', r'\boi\d+_\d_(\w+)']:
        match = re.search(pattern, a['href'])
        if match is not None:
          codes.append(match[1])
    code = codes[0]
    assert all(code == i for i in codes), row

    id = f'oi{olympiad}-{code}'
    name = cols[0].text.strip()
    stage = {
      'Etap I':                    'I etap',
      'Etap I, tura szkolna':      'I etap',
      'Etap I, tura zdalna':       'I etap',
      'Etap II - dzień próbny':    'próbny II etap',
      'Etap II, dzień próbny':     'próbny II etap',
      'Etap II - dzień pierwszy':  'II etap',
      'Etap II, dzień pierwszy':   'II etap',
      'Etap II - dzień drugi':     'II etap',
      'Etap II, dzień drugi':      'II etap',
      'Etap III - dzień próbny':   'próbny finał',
      'Etap III, dzień próbny':    'próbny finał',
      'Etap III - dzień pierwszy': 'finał',
      'Etap III, dzień pierwszy':  'finał',
      'Etap III - dzień drugi':    'finał',
      'Etap III, dzień drugi':     'finał',
    }[cols[1].text.strip()]

    problems.append([id, name, competition, stage, url])

for problemset_url, problemset_stage, stage_num in [
  ('https://oij.edu.pl/zbior_zadan/etap1/', 'I etap', '1'),
  ('https://oij.edu.pl/zbior_zadan/etap2/', 'II etap', '2'),
  ('https://oij.edu.pl/zbior_zadan/etap3/', 'finał', '3'),
]:
  response = requests.get(problemset_url)
  response.raise_for_status()
  html = BeautifulSoup(response.content, 'lxml')

  url, olympiad, competition = None, None, None
  for elem in html.article.children:
    if elem.name == 'h3':
      url = f'{problemset_url}#{elem["id"]}'
      olympiad = int(elem['id'].removeprefix('oij-'))
      competition = f'{to_roman_numeral(olympiad)} OIJ'

    if elem.name != 'ul':
      continue

    for item in elem.find_all('li', recursive=False):
      code = re.search(r'\w+', list(item.stripped_strings)[1])[0]
      id = f'oij{olympiad}-{stage_num}-{code}'
      name = item.a.text.strip()
      stage = problemset_stage
      if name.endswith('(zadanie próbne)'):
        name = name.removesuffix('(zadanie próbne)').rstrip()
        stage = f'próbny {stage}'
      problems.append([id, name, competition, stage, url])

problems.sort()

assert len({problem[0] for problem in problems}) == len(problems)

with open('problems.csv', 'w', newline='') as file:
  writer = csv.writer(file)
  writer.writerow(['id', 'name', 'competition', 'stage', 'url'])
  writer.writerows(problems)
