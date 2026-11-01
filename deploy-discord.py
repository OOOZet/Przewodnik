#!/usr/bin/env -S /bin/sh -c 'exec "$(dirname "$0")/venv/bin/python3" "$0" "$@"'

import discord, sys
from argparse import ArgumentParser
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
  entity_refs = {}

  for i, entity in enumerate(document):
    print(f'Processing entity {i + 1} of {len(document)}...')
    match entity.tag:
      case 'channel-topic':
        assert len(entity) == 0, entity
        await chan.edit(topic=entity.text)

      case 'message':
        content = entity.text.lstrip()
        files = []

        for node in entity:
          match node.tag:
            case 'anchor':
              anchor_entity[node.attrib['id']] = entity

            case 'file':
              files.append(discord.File(node.attrib['src'], node.attrib['name']))

            case 'ref':
              longest_snowflake = str(2**64 - 1)
              start = len(content)
              content += f'https://discord.com/channels/{longest_snowflake}/{longest_snowflake}/{longest_snowflake}'
              end = len(content)
              entity_refs.setdefault(entity, []).append((start, end, node.attrib['id']))

            case _:
              raise Exception(f'Unknown tag in message: {node.tag!r}')
          content += node.tail

        entity_msg[entity] = await chan.send(content, files=files, suppress_embeds=True)

      case _:
        raise Exception(f'Unknown entity: {entity.tag!r}')

  for i, (entity, refs) in enumerate(entity_refs.items()):
    msg = entity_msg[entity]
    print(f'Patching message {i + 1} of {len(entity_refs)}...')

    refs.sort(key=lambda x: x[1], reverse=True)
    content = msg.content
    for start, end, id in refs:
      content = content[:start] + entity_msg[anchor_entity[id]].jump_url + content[end:]
    await msg.edit(content=content, suppress=True)

  await client.close()

client.run(args.token)
