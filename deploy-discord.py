#!/usr/bin/env -S /bin/sh -c 'exec "$(dirname "$0")/venv/bin/python3" "$0" "$@"'
#
# Przewodnik OOOZ
# Copyright (C) 2026 Karol "digitcrusher" Łacina
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import discord, sys
from argparse import ArgumentParser
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from io import StringIO
from xml.etree import ElementTree

parser = ArgumentParser()
parser.add_argument('--token', required=True)
parser.add_argument('--guild', required=True)
parser.add_argument('--channel', required=True)
parser.add_argument('--purge', action='store_true')
args = parser.parse_args()

document = ElementTree.parse('build/discord.xml').getroot()

client = discord.Client(
  intents=discord.Intents.default(),
  allowed_mentions=discord.AllowedMentions.none(),
)

@dataclass
class Ref:
  start: int
  end: int
  id: str

def append_ref(content, ref_node):
  longest_snowflake = str(2**64 - 1)
  start = len(content)
  content += f'https://discord.com/channels/{longest_snowflake}/{longest_snowflake}/{longest_snowflake}'
  end = len(content)
  return content, Ref(start, end, ref_node.attrib['id'])

@dataclass
class Patchable:
  content: str
  refs: list[Ref]
  callback: Callable[[str], Awaitable[None]]

@client.event
async def on_ready():
  guild = await client.fetch_guild(args.guild)
  chan = await guild.fetch_channel(args.channel)
  print(f'Deploying document to channel {str(chan)!r} in guild {str(guild)!r}...')

  if args.purge:
    prompt = 'Do you really want to \x1b[1merase all messages\x1b[0m from the aforementioned channel? (Yes/No) '
    match input(prompt).lower():
      case 'yes':
        await chan.purge(limit=None)
        print('Erased.')
      case _:
        print('Answer not "yes". Aborting.')
        await client.close()
        return

  anchor_entity = {}
  entity_msg = {}
  to_patch = []

  for i, entity in enumerate(document):
    print(f'Processing entity {i + 1} of {len(document)}...')
    match entity.tag:
      case 'channel-topic':
        content = entity.text.lstrip()
        refs = []

        for node in entity:
          match node.tag:
            case 'ref':
              content, ref = append_ref(content, node)
              refs.append(ref)
          content += node.tail

        await chan.edit(topic=content)

        if refs:
          async def callback(content):
            await chan.edit(topic=content)
          to_patch.append(Patchable(content, refs, callback))

      case 'message':
        content = entity.text.lstrip()
        refs = []
        files = []

        for node in entity:
          match node.tag:
            case 'anchor':
              anchor_entity[node.attrib['id']] = entity
            case 'file':
              files.append(discord.File(
                node.attrib.get('src', StringIO(node.text)),
                node.attrib.get('name'),
                description=node.attrib.get('description'),
              ))
            case 'ref':
              content, ref = append_ref(content, node)
              refs.append(ref)
          content += node.tail

        msg = entity_msg[entity] = await chan.send(content, files=files, suppress_embeds=True)

        if refs:
          def closure(msg):
            async def callback(content):
              await msg.edit(content=content, suppress=True)
            return callback
          to_patch.append(Patchable(content, refs, closure(msg)))

  for i, patchable in enumerate(to_patch):
    print(f'Patching entity {i + 1} of {len(to_patch)}...')
    patchable.refs.sort(key=lambda x: x.end, reverse=True)
    content = patchable.content
    for ref in patchable.refs:
      content = content[:ref.start] + entity_msg[anchor_entity[ref.id]].jump_url + content[ref.end:]
    await patchable.callback(content)

  await client.close()

client.run(args.token)
