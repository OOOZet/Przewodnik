{#
 # Being extra nitpicky about generated whitespace helps keep
 # the output Typst code human-readable and easier to debug.
 #}

{% macro render_block(node) %}
  {% if node.tag == 'code' %}
{{ render_code(node, true) }}
  {% elif node.tag == 'list' %}
#list(
    {% for item in node.findall('item') %}
[
{{ render_blocks(item) }}
],
    {% endfor %}
)
  {% elif node.tag == 'note' %}
#note[
{{ render_blocks(node) }}
]
  {% elif node.tag == 'todo' %}
#todo[
{{ render_blocks(node) }}
]
  {% elif node.tag == 'paragraph' %}
{{ render_inlines(node) | escape_typst_line_markup }}
  {% elif node.tag == 'subanswer' %}
== {{ render_text(node.attrib['subquestion']) }}
    {% if 'id' in node.attrib %}
#label({{ node.attrib['id'] | escape_typst_string }})
    {% endif %}
{{ render_blocks(node) }}
  {% elif node.tag == 'warning' %}
#warning[
{{ render_blocks(node) }}
]
  {% else %}
    {{ error('Unknown block tag: ' ~ repr(node.tag)) }}
  {% endif %}
{% endmacro %}

{% macro render_inline(node) %}
  {% if node.tag == 'code' -%}
    {{ render_code(node, false) }}
  {%- elif node.tag == 'emphasis' -%}
    _{{ render_inlines(node) }}_
  {%- elif node.tag == 'important' -%}
    *{{ render_inlines(node) }}*
  {%- elif node.tag == 'link' -%}
    #link({{ node.attrib['url'] | escape_typst_string }})[{{ render_inlines(node) }}]
  {%- elif node.tag == 'placeholder' -%}
    {{ placeholder_values[node.attrib['for']] }}
  {%- elif node.tag == 'ref' -%}
    #link(label({{ node.attrib['id'] | escape_typst_string }}))[{{ render_inlines(node) }}]
  {%- else %}
    {{ error('Unknown inline tag: ' ~ repr(node.tag)) }}
  {% endif %}
{% endmacro %}

{% macro render_code(node, is_block) %}
#raw(block: {{ is_block | lower }},
{%- if 'lang' in node.attrib %}
lang: {{ node.attrib['lang'] | escape_typst_string }}, {% endif %}
{{ node.text | escape_typst_string }})
{%- endmacro %}

{% macro render_text(text) %}{{ (text or '').replace(' - ', ' --- ') | escape_typst_markup }}{% endmacro %}

{% macro render_blocks(node) %}
  {% for child in node %}
{{ render_block(child) }}
  {% endfor %}
{% endmacro %}

{% macro render_inlines(node) %}
{{ render_text(node.text) }}{% for child in node %}{{ render_inline(child) }}{{ render_text(child.tail) }}{% endfor %}
{% endmacro %}

{% set contributors %}
  {% for node in document.findall('contributor') %}
    {% if 'website' in node.attrib %}
#link({{ node.attrib['website'] | escape_typst_string }})[
    {%- endif %}
{{ node.attrib['name'] | escape_typst_markup }}
    {%- if 'website' in node.attrib %}
]
    {%- endif %}
 ({{ node.attrib['contribution'] }})
    {%- if not loop.last %}, {% endif %}
  {% endfor %}
{% endset %}
{% set placeholder_values = {
  'contributors': contributors,
} %}

#set document(
  title: [{{ render_text(document.attrib['title']) }}],
{% if 'version' in document.attrib %}
  {% set version = datetime.fromisoformat(document.attrib['version']) %}
  date: datetime(year: {{ version.year }}, month: {{ version.month }}, day: {{ version.day }}),
{% else %}
  date: none,
{% endif %}
)

// Typography
#let heading-font = "Inter Display"
#set text(font: "Inter", weight: 300, size: 10pt)
#show heading: set text(font: heading-font)
#show heading.where(level: 1): set text(size: 16pt)
#show heading.where(level: 2): set text(size: 14pt)
#show raw: set text(font: "Roboto Mono", weight: 320, size: 10.26pt)
#show raw.where(block: true): set text(weight: 330)
#show title: set text(font: heading-font, size: 30pt)

// Spacing
#let block-inset = 1em
#let section-break() = v(1.5cm, weak: true)
#set par(spacing: 1.4em)
#show heading: set block(above: 1.2em, below: 1em)

// Text flow
#set par(justify: true)
#set text(lang: "pl")
#show "C++": box
#show regex(`\W\w `.text): it => [#it.text.trim(at: end)~]

// Other
#set list(marker: ([•], [◦]))
#show link: set text(blue)
#show raw.where(block: true): set align(center)
#show raw.where(block: true): set block(fill: color.luma(97%), inset: block-inset)

// Macros and symbols
#let highlight-block(hue, icon, hint, content) = block(
  fill: color.oklch(95%, 30%, hue),
  width: 100%,
  inset: block-inset,
  [
    #block(sticky: true, text(fill: color.oklch(70%, 80%, hue), size: 8pt, font: heading-font, strong([
      #text(font: "Material Symbols Sharp", variations: (FILL: 1), baseline: 1pt, icon) #hint
    ])))
    #v(0.9em, weak: true)
    #content
  ]
)
#let note(content) = highlight-block(260deg, [\u{e88e}], [Pamiętaj...], content)
#let warning(content) = highlight-block(80deg, [\u{e002}], [Uważaj!], content)
#let todo(content) = block(
  fill: tiling(size: (1cm, 1cm), {
    place(square(fill: black, width: 100%))
    place(polygon(fill: yellow, (100%, 0%), (50%, 0%), (0%, 50%), (0%, 100%)))
    place(polygon(fill: yellow, (100%, 50%), (100%, 100%), (50%, 100%)))
  }),
  width: 100%,
  inset: 75% * block-inset,
  {
    set align(center)
    show: rest => block(fill: black.transparentize(25%), inset: 50% * block-inset, rest)
    set text(white, weight: 400)
    content
  },
)
#show ">=": [≥]

#align(center)[
  #set par(justify: false)

  #title()

  {% if 'version' in document.attrib %}
  #text(font: heading-font)[{{ document.attrib['version'] | human_date }}]
  {% endif %}

  #section-break()

  {{ render_blocks(document.find('preface')) }}

  #section-break()

  #show outline.entry: it => {
    let loc = it.element.location()
    let metadata = query(selector(metadata).within(loc)).at(0).value
    let result = link(loc, it.indented(it.prefix(), it.body()))
    if metadata.important { strong(result) } else { result }
  }
  #outline(depth: 1)
]

#pagebreak()

{% for node in document.findall('answer') %}
= {{ render_text(node.attrib['question']) }} #metadata(
  (important: {{ (node.attrib.get('important') == 'yes') | lower }}),
)
  {% if 'id' in node.attrib %}
#label({{ node.attrib['id'] | escape_typst_string }})
  {% endif %}

{{ render_blocks(node) }}

#section-break()
{% endfor %}

#align(center)[
  #set par(justify: false)
  {{ render_blocks(document.find('footer')) }}
]
