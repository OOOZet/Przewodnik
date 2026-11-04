#!/usr/bin/env -S /bin/sh -c 'exec "$(dirname "$0")/venv/bin/python3" "$0" "$@"'

# TODO: Integrate spell checker
# IDEA: Show tooltips for competitive programming jargon
# IDEA: Schematron schema
# IDEA: Changelog

import csv, htmlmin, lxml, markupsafe, os, pygments, re, shutil, subprocess, sys, unicodedata
from argparse import ArgumentParser
from bs4 import BeautifulSoup
from collections import namedtuple
from contextlib import contextmanager
from datetime import datetime
from enum import auto, Enum
from jinja2 import Environment, FileSystemLoader
from lxml.etree import RelaxNG
from markupsafe import Markup
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.style import Style
from pygments.token import Comment, Keyword, Name, Number, Operator, String
from pyphen import Pyphen
from rcssmin import cssmin
from threading import Event
from watchdog.events import RegexMatchingEventHandler
from watchdog.observers import Observer
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

def main():
  os.chdir(sys.path[0])
  parser = ArgumentParser()
  parser.add_argument('--watch', action='store_true', help='rebuilds on any change in the project directory')
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
      sys.stderr.write('\x1b[2J\n\n\n\x1b[1;1H')
      log_info(f'Running build now at {datetime.now()}')
      subprocess.run([sys.executable, __file__])
      log_info('Waiting for changes to source files')
      # We don't clear before building because formatting source.xml overwrites it.
      change_event.clear()
      change_event.wait()
  except KeyboardInterrupt:
    pass

def build():
  format_text_file('source.xml')

  validate_source()

  log_info('Creating build directory')
  try:
    os.mkdir('build')
  except FileExistsError:
    pass

  log_info('Building for Discord')
  with log_indent():
    preprocess_source(Target.discord)

    render(Target.discord)

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

  log_info('Building webpage')
  with log_indent():
    preprocess_source(Target.webpage)

    render(Target.webpage)

    minify_html('build/webpage.html')

    log_info('Structuring output directory')
    os.makedirs('build/webpage/', exist_ok=True)
    os.rename('build/webpage.html', 'build/webpage/index.html')
    shutil.copy('build/download.pdf', 'build/webpage/Przewodnik OOOZ.pdf')

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
          try:
            name = ' ' + unicodedata.name(c)
          except ValueError:
            name = ''
          log_error(f'Found U+{ord(c):04X}{name} at {line}:{col}')
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

def validate_source():
  log_info('Validating source')
  with log_indent():
    relax_ng = RelaxNG(file='source.rnc')
    if relax_ng.validate(lxml.etree.parse('source.xml')):
      return
    for error in relax_ng.error_log:
      assert error.level_name == 'ERROR', error
      msg = f'Line {error.line}'
      if error.column != 0:
        msg += f', column {error.column}'
      msg += f': {error.message}'
      log_error(msg)
    sys.exit(1)

def preprocess_source(target):
  log_info('Preprocessing source')
  with log_indent():
    source = ElementTree.parse('source.xml')

    set_document_version(source)

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

    os.makedirs('build/source/', exist_ok=True)
    source.write(f'build/source/{target.name}.xml')

def set_document_version(source):
  log_info('Getting version from git')
  document = source.getroot()
  dirty_check = subprocess.run(['git', 'diff', '--quiet', 'HEAD'])
  if dirty_check.returncode == 0:
    stdout = subprocess.run(
      ['git', 'log', '-1', '--format=%H%x00%cd', '--date=iso-strict'],
      stdout=subprocess.PIPE,
      check=True,
    ).stdout.decode()
    document.attrib['git-commit'], document.attrib['version'] = stdout.strip().split('\0')
  else:
    try:
      del document.attrib['version']
    except KeyError:
      pass

def expand_conditionals(parent, target):
  if parent.text is None:
    parent.text = ''

  i = 0
  while i < len(parent):
    child = parent[i]
    expand_conditionals(child, target)
    if not child.tag.endswith('-only'):
      i += 1
      continue

    del parent[i]
    is_kept = child.tag.removesuffix('-only') == target.name or \
              child.tag == 'external-only' and target in {Target.download, Target.webpage}

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
      'problem',
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
    Target.discord: 'discord.xml',
    Target.download: 'download.typ',
    Target.webpage: 'webpage.html',
  }[target]
  log_info(f'Rendering {template_name}')

  source = ElementTree.parse(f'build/source/{target.name}.xml')

  problems = {}
  with open('problems.csv', 'r', newline='') as f:
    reader = csv.reader(f)
    Problem = namedtuple('Problem', next(reader))
    for row in reader:
      problem = Problem._make(row)
      problems[problem.id] = problem

  env = Environment(
    loader=FileSystemLoader('templates'),
    # Autoescaping escapes only HTML tags, which obviously is not only
    # insufficient but also harmful to our needs in the case of Typst.
    autoescape=False,
    lstrip_blocks=True,
    trim_blocks=True,
  )
  env.globals |= {
    'datetime': datetime,
    'ElementTree': ElementTree,
    'embed_file': embed_file,
    'error': error,
    'highlights_css': highlights_css,
  }
  env.filters |= {
    'escape_discord_code_block': escape_discord_code_block,
    'escape_discord_line_markup': escape_discord_line_markup,
    'escape_discord_markup': escape_discord_markup,
    'escape_discord_url': escape_discord_url,
    'escape_typst_line_markup': escape_typst_line_markup,
    'escape_typst_markup': escape_typst_markup,
    'escape_typst_string': escape_typst_string,
    'expand_xml_tags': expand_xml_tags,
    'fix_discord_link_label': fix_discord_link_label,
    'highlight': highlight,
    'human_date': human_date,
    'hyphenate': hyphenate,
    'render_ascii_approximations': render_ascii_approximations,
    'render_nonbreaking_spaces': render_nonbreaking_spaces,
    'split_long_discord_message': split_long_discord_message,
    'repr': repr,
  }

  out = env.get_template(template_name).render(document=source.getroot(), problems=problems)
  with open(f'build/{template_name}', 'w') as f:
    f.write(out)

def highlights_css(parent_selector):
  return HtmlFormatter(style=TypstLight).get_style_defs(parent_selector)

def embed_file(path):
  with open(path, 'r') as f:
    return Markup(f.read())

def error(s):
  raise Exception(s)

def escape_discord_code_block(code):
  return code.replace('```', '`\u2060`\u2060`')

def escape_discord_line_markup(string):
  root = ElementTree.fromstring(f'<root>{markupsafe.escape(string)}</root>')
  apply_regex = lambda init_char, text: re.sub(
    r'(' + init_char + r'\s*)(?:(\d+)(?=\.)|(?=#+ |[->] ))', r'\1\2\\', text,
  )
  if root.text is not None:
    root.text = apply_regex(r'^', root.text)
  for node in root:
    if node.tail is not None:
      node.tail = apply_regex(r'\n', node.tail)
  return Markup(ElementTree.tostring(root, 'unicode').removeprefix('<root>').removesuffix('</root>'))

def escape_discord_markup(text):
  return re.sub(r'(?=[*[\\_`~])', r'\\', text)

def escape_discord_url(text):
  return re.sub(r'(?=[)\\])', r'\\', text)

def escape_typst_line_markup(text):
  return re.sub(r'^(\s*)(?=[+-/] |=+ )', r'\1\\', text)

def escape_typst_markup(text):
  return re.sub(r'(?=[#$*<>@[\\\]_`~])', r'\\', text)

def escape_typst_string(text):
  return '"' + re.sub(r'(?=["\\])', r'\\', text) + '"'

def expand_xml_tags(string, tag):
  root = ElementTree.fromstring(f'<root>{markupsafe.escape(string)}</root>')
  _expand_xml_tags(root, tag)
  return Markup(ElementTree.tostring(root, 'unicode').removeprefix('<root>').removesuffix('</root>'))

def _expand_xml_tags(parent, tag):
  if parent.text is None:
    parent.text = ''

  i = 0
  while i < len(parent):
    child = parent[i]
    _expand_xml_tags(child, tag)
    if child.tag != tag:
      i += 1
      continue

    del parent[i]

    if child.text is not None:
      if i == 0:
        parent.text += child.text
      else:
        sibling = parent[i - 1]
        sibling.tail = ('' if sibling.tail is None else sibling.tail) + child.text

    for grandchild in child:
      parent.insert(i, grandchild)
      i += 1

    if child.tail is not None:
      if i == 0:
        parent.text += child.tail
      else:
        sibling = parent[i - 1]
        sibling.tail = ('' if sibling.tail is None else sibling.tail) + child.tail

def fix_discord_link_label(markup):
  # Basically, we try to unrender non-breaking spaces and unescape markup that
  # doesn't need escaping in this context. The selection thereof is definitely
  # incomplete here.
  return markup.replace('\xa0', ' ').replace('\\[', '[')

def highlight(code, lang):
  formatter = HtmlFormatter(style=TypstLight, nowrap=True)
  return Markup(pygments.highlight(code, get_lexer_by_name(lang), formatter))

# BUG: Pygments' and syntect's (used by Typst) differ visibly in the token types they detect.
# WARNING: This is by no means a complete translation of Typst's theme
#          and it omits many tokens, which we didn't need at the time.
# Based on: https://github.com/typst/typst/blob/64c5e8c/crates/typst-library/src/text/raw.rs#L1097
class TypstLight(Style):
  name = 'typst_light'
  styles = {
    Comment: '#74747c',
    Comment.Preproc: '#d73948',
    Comment.PreprocFile: '#198810',
    Keyword: '#d73948',
    Name.Builtin: '#4b69c6',
    Name.Class: '#4b69c6',
    Name.Decorator: '#4b69c6',
    Name.Function: '#4b69c6',
    Number: '#b60157',
    Operator: '#d73948',
    String: '#198810',
    String.Affix: '#d73948',
    String.Doc: '#74747c',
    String.Escape: '#1d6c76',
    String.Interpol: '#8b41b1',
  }

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
  dt = datetime.fromisoformat(iso_date).astimezone(ZoneInfo('Europe/Warsaw'))
  return f'{dt.day} {months[dt.month - 1]} {dt.year}'

def hyphenate(text):
  result = Pyphen(lang='pl', cache=True).inserted(text, '\xad')
  for pattern, repl in [(r'\xad\B', ''), (r'\b(\w)\xad', r'\1'), (r'\xad(\w)\b', r'\1')]:
    result = re.sub(pattern, repl, result)
  return result

def render_ascii_approximations(text):
  for pattern, repl in [
    (r'\B"\b', '„'),
    (r'\b"\B', '”'),
    (r"\B'\b", '‚'),
    (r'(?<=\s)-(?=\s)', '—'),
  ]:
    text = re.sub(pattern, repl, text)
  for pattern, repl in [
    ("'", '’'), # This replaces both closing single quotation marks and apostrophes.
    ('...', '…'),
    ('>=', '≥'),
  ]:
    text = text.replace(pattern, repl)
  return text

def render_nonbreaking_spaces(text):
  return re.sub(r'(?<=\b\w) ', '\xa0', text)

def split_long_discord_message(string):
  longest_snowflake = str(2**64 - 1)
  max_ref_len = len(f'https://discord.com/channels/{longest_snowflake}/{longest_snowflake}/{longest_snowflake}')
  lines = line_wrap_xml(string, 2000, {
    'ref': lambda _: max_ref_len,
  })
  return Markup('<message>' + '</message><message>'.join(lines) + "</message>")

def line_wrap_xml(string, max_line_len, len_funcs={}):
  lines = [[[], 0]]

  def append_breakable(text):
    while text:
      if lines[-1][1] + len(text) <= max_line_len:
        lines[-1][0].append(text)
        lines[-1][1] += len(text)
        text = ''
      else:
        cutoff = max_line_len - lines[-1][1]
        head, sep, tail = text[:cutoff].rpartition(' ')
        if sep:
          lines[-1][0].append(head)
          lines[-1][1] += len(head)
          lines.append([[], 0])
          text = tail + text[cutoff:]
        elif lines[-1]:
          lines.append([[], 0])
        else:
          head, _, text = text.partition(' ')
          lines[-1] = [[head], len(head)]

  def append_unbreakable(string, printable_len):
    if lines[-1][1] + printable_len <= max_line_len:
      lines[-1][0].append(string)
      lines[-1][1] += printable_len
    else:
      lines.append([[string], printable_len])

  root = ElementTree.fromstring(f'<root>{markupsafe.escape(string)}</root>')
  if root.text is not None:
    append_breakable(root.text)

  for node in root:
    tail = node.tail
    node.tail = None

    if node.tag in len_funcs:
      printable_len = len_funcs[node.tag](node)
    else:
      printable_len = xml_content_len(node, len_funcs)
    append_unbreakable(Markup(ElementTree.tostring(node, 'unicode')), printable_len)

    if tail is not None:
      append_breakable(tail)

  if not lines[-1][0]:
    lines.pop()

  return [Markup(''.join(markupsafe.escape(i) for i in parts)) for parts, _ in lines]

def xml_content_len(node, len_funcs):
  result = 0 if node.text is None else len(node.text)
  for child in node:
    if child.tag in len_funcs:
      result += len_funcs[child.tag](child)
    else:
      result += xml_content_len(child, len_funcs)
    result += 0 if child.tail is None else len(child.tail)
  return result

def minify_html(path):
  log_info(f'Minifying {path!r}')
  with open(path, 'r') as f:
    html = f.read()
  html = BeautifulSoup(html, 'lxml')
  for node in html.find_all('style'):
    node.string = cssmin(node.string)
  html = htmlmin.minify(str(html), remove_comments=True, remove_empty_space=True)
  with open(path, 'w') as f:
    f.write(html)

class Target(Enum):
  discord = auto()
  download = auto()
  webpage = auto()

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
