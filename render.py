#!/usr/bin/env python3

import os, sys, unicodedata
from contextlib import contextmanager

def main():
  format_text_file('source.xml')

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
