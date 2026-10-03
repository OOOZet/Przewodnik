#!/usr/bin/env python3

import os, re, subprocess, sys, unicodedata
from argparse import ArgumentParser
from contextlib import contextmanager
from datetime import datetime
from enum import auto, Enum
from jinja2 import Environment, FileSystemLoader
from threading import Event
from watchdog.events import RegexMatchingEventHandler
from watchdog.observers import Observer
from xml.etree import ElementTree

def main():
  os.chdir(sys.path[0])
  parser = ArgumentParser()
  parser.add_argument('--watch', action='store_true')
  args = parser.parse_args()
  if args.watch:
    watch()
  else:
    build()

def watch():
  change_event = Event()
  class Handler(RegexMatchingEventHandler):
    def on_any_event(self, event):
      if event.event_type not in {'closed_no_write', 'modified', 'opened'}:
        change_event.set()

  observer = Observer()
  observer.daemon = True
  observer.schedule(Handler(ignore_regexes=[
    r'\./\.git.*',
    r'\./build/.*',
    r'\./README.md',
    r'\./requirements.txt',
  ]), '.', recursive=True)
  observer.start()

  try:
    while True:
      sys.stderr.write('\x1b[2J\x1b[1;1H')
      log_info(f'Running build now at {datetime.now()}')
      subprocess.run([__file__])
      log_info('Waiting for changes to source files')
      # We don't clear before building because formatting source.xml overwrites it.
      change_event.clear()
      change_event.wait()
  except KeyboardInterrupt:
    pass

def build():
  format_text_file('source.xml')

  log_info('Creating build directory')
  try:
    os.mkdir('build')
  except FileExistsError:
    pass

  log_info('Building for Discord')
  with log_indent():
    preprocess_source(Target.discord)

  log_info('Building downloadable file')
  with log_indent():
    preprocess_source(Target.download)

    render(Target.download)

    log_info('Compiling download.typ')
    typst = subprocess.run([
      'typst', 'compile', 'build/download.typ',
      '--root', '.',
      '--font-path', 'fonts',
      '--ignore-system-fonts', # Uncomment this, if you want to use fonts installed on your system.
    ])
    if typst.returncode != 0:
      sys.exit(1)

def format_text_file(path):
  log_info(f'Formatting {path!r}')
  with log_indent():
    with open(path, 'r') as f:
      old = f.read()
      new = old

    log_info('Trimming trailing whitespace')
    new = ''.join(line.rstrip() + '\n' for line in new.strip().splitlines())

    log_info('Normalizing Unicode characters')
    new = unicodedata.normalize('NFKC', new)

    log_info('Searching for forbidden Unicode characters')
    with log_indent():
      permitted_ranges = [
        (0x00a, 0x00a), # Line Feed
        (0x020, 0x07e), # Printable ASCII
        (0x0c0, 0x0d6), # Latin-1 Supplement - Letters
        (0x0d8, 0x0f6),
        (0x0f8, 0x0ff),
        (0x100, 0x148), # Latin Extended-A - European Latin
        (0x14a, 0x17f),
        (0x3b1, 0x3c1), # Standard forms of Modern Greek lowercase letters
        (0x3c3, 0x3c9),
      ]
      had_errors = False
      line, col = 1, 1
      for c in new:
        if not any(a <= ord(c) <= b for a, b in permitted_ranges):
          log_error(f'Found U+{ord(c):04X} {unicodedata.name(c)} at {line}:{col}')
          had_errors = True
        if c == '\n':
          line += 1
          col = 1
        else:
          col += 1
      if had_errors:
        raise Exception(f'{path!r} contains forbidden Unicode characters. Contact the maintainers, if you believe this is a mistake.')

    if new == old:
      log_info('Nothing changed')
    else:
      with open(f'{path}.new', 'w') as f:
        f.write(new)
      os.rename(f'{path}.new', path)
      log_notice('Overwritten')

def preprocess_source(target):
  log_info(f'Preprocessing source')
  with log_indent():
    source = ElementTree.parse('source.xml')

    log_info('Expanding conditionals')
    expand_conditionals(source.getroot(), target)

    log_info('Splitting text into paragraphs')
    block_xpaths = [
      './/answer',
      './/footer',
      './/list/item',
      './/note',
      './/preface',
      './/subanswer',
      './/todo',
      './/warning',
    ]
    for xpath in block_xpaths:
      for node in source.findall(xpath):
        split_into_paragraphs(node)

    log_info('Normalizing whitespace')
    text_xpaths = {
      './/emphasis',
      './/important',
      './/link',
      './/paragraph',
      './/ref',
    }
    for xpath in text_xpaths:
      for node in source.findall(xpath):
        normalize_whitespace(node)

    log_info('Trimming whitespace in "code" nodes')
    for node in source.findall('.//code'):
      node.text = node.text.strip()

    source.write(f'build/{target.name}.xml')

def expand_conditionals(parent, target):
  i = 0
  while i < len(parent):
    child = parent[i]
    expand_conditionals(child, target)
    if not child.tag.endswith('-only'):
      i += 1
      continue

    del parent[i]
    is_kept = child.tag.removesuffix('-only') == target.name

    if is_kept and child.text is not None:
      if i == 0:
        parent.text += child.text
      else:
        sibling = parent[i - 1]
        sibling.tail = ('' if sibling.tail is None else sibling.tail) + child.text

    if is_kept:
      for grandchild in child:
        parent.insert(i, grandchild)
        i += 1

    if child.tail is not None:
      if i == 0:
        parent.text += child.tail
      else:
        sibling = parent[i - 1]
        sibling.tail = ('' if sibling.tail is None else sibling.tail) + child.tail

def split_into_paragraphs(parent):
  children = list(parent)
  while len(parent) > 0:
    del parent[0] # Ughh...

  paragraph = None

  def flush():
    nonlocal paragraph
    if paragraph is not None:
      if len(paragraph) > 0:
        paragraph[-1].tail = paragraph[-1].tail.rstrip()
      else:
        paragraph.text = paragraph.text.rstrip()
      parent.append(paragraph)
      paragraph = None

  def begin():
    nonlocal paragraph
    if paragraph is None:
      paragraph = ElementTree.Element('paragraph')
      paragraph.text = ''

  def append(text):
    if text is None:
      return

    if paragraph is None:
      text = text.lstrip()
    elif len(paragraph) > 0:
      text = paragraph[-1].tail + text
      paragraph[-1].tail = ''
    else:
      text = paragraph.text + text
      paragraph.text = ''

    while text:
      tail, sep, text = text.partition('\n\n')
      begin()
      if len(paragraph) > 0:
        paragraph[-1].tail += tail
      else:
        paragraph.text += tail
      if not sep:
        break
      text = text.lstrip()
      flush()

  append(parent.text)
  parent.text = None
  for child in children:
    inline_tags = {
      'emphasis',
      'important',
      'link',
      'placeholder',
      'ref',
    }
    block_or_inline_tags = {
      'code',
    }
    if child.tag in inline_tags or paragraph is not None and child.tag in block_or_inline_tags:
      begin()
      paragraph.append(child)
      text = child.tail
      child.tail = ''
      append(text)
    else:
      flush()
      parent.append(child)
      append(child.tail)
      child.tail = None
  flush()

def normalize_whitespace(node):
  if node.text is not None:
    node.text = re.sub(r'\s+', ' ', node.text)
  for child in node:
    if child.tail is not None:
      child.tail = re.sub(r'\s+', ' ', child.tail)

def render(target):
  template_name = {
    Target.download: 'download.typ',
  }[target]
  log_info(f'Rendering {template_name}')

  tree = ElementTree.parse(f'build/{target.name}.xml')
  env = Environment(
    loader=FileSystemLoader('templates'),
    # Autoescaping escapes only HTML tags, which obviously
    # is not only insufficient but also harmful to our needs.
    autoescape=False,
    lstrip_blocks=True,
    trim_blocks=True,
  )
  def error(s):
    raise Exception(s)
  env.globals |= {
    'datetime': datetime,
    'error': error,
    'repr': repr,
  }
  env.filters |= {
    'escape_typst_line_markup': escape_typst_line_markup,
    'escape_typst_markup': escape_typst_markup,
    'escape_typst_string': escape_typst_string,
    'human_date': human_date,
  }

  out = env.get_template(template_name).render(document=tree.getroot())
  with open(f'build/{template_name}', 'w') as f:
    f.write(out)

def escape_typst_line_markup(text):
  return re.sub(r'^(\s*)([+-/=]) ', r'\1\\\2 ', text)

def escape_typst_markup(text):
  return re.sub(r'([#$*<>@[\\\]_`~])', r'\\\1', text)

def escape_typst_string(text):
  return '"' + re.sub(r'(["\\])', r'\\\1', text) + '"'

def human_date(iso_date):
  months = [
    'stycznia',
    'lutego',
    'marca',
    'kwietnia',
    'maja',
    'czerwca',
    'lipca',
    'sierpnia',
    'września',
    'października',
    'listopada',
    'grudnia',
  ]
  dt = datetime.fromisoformat(iso_date)
  return f'{dt.day} {months[dt.month - 1]} {dt.year}'

class Target(Enum):
  discord = auto()
  download = auto()

def log_info(msg):
  log_any(msg, None)

def log_notice(msg):
  log_any(msg, '\x1b[1m')

def log_warning(msg):
  log_any(msg, '\x1b[33m')

def log_error(msg):
  log_any(msg, '\x1b[31m')

log_indent_level = 0

@contextmanager
def log_indent():
  global log_indent_level
  log_indent_level += 1
  try:
    yield
  finally:
    log_indent_level -= 1

def log_any(msg, color_code):
  if color_code is not None:
    msg = color_code + msg + '\x1b[0m'
  if log_indent_level > 0:
    msg = '  ' * (log_indent_level - 1) + '\\ ' + msg
  sys.stderr.write(msg + '\n')

if __name__ == '__main__':
  main()
