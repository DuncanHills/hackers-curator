import errno
import os
import textwrap
from pathlib import Path
from typing import AnyStr, List, NamedTuple, Dict

import click
from jinja2 import Template
import pandas
from pandas import DataFrame

help_message = (
  'Process an input file into individual Hackers fashion entries.'
)


@click.command(short_help=help_message)
@click.option('--excel-path',
              help='Path to input Excel spreadsheet.',
              type=click.Path(dir_okay=False,
                              readable=True),
              required=True)
@click.option('--images-directory',
              help='Path to fashion images directory.',
              type=click.Path(file_okay=False,
                              writable=True),
              required=True)
@click.option('--output-directory',
              help='Path to fashion files output directory.',
              type=click.Path(file_okay=False,
                              writable=True),
              required=True)
def fashion_files(
    excel_path: AnyStr,
    images_directory: AnyStr,
    output_directory: AnyStr
) -> None:
  dataframes = import_excel_as_dataframe(excel_path)
  for (character, dataframe) in dataframes.items():
    fashion_entries = dataframe_to_fashion_entries(dataframe)
    print(fashion_entries)
    character_path = Path(output_directory) / character.capitalize()
    mkdirs_safe(character_path)
    for entry in fashion_entries:
      entry_image_paths = get_image_paths(character, entry, Path(images_directory))
      html = render_fashion_entry_html(
        character=character,
        fashion_entry=entry,
        image_paths=entry_image_paths
      )
      entry_path = character_path / (entry.id + '.txt')
      with open(entry_path, 'w+') as entry_output_file:
        entry_output_file.write(html)


FashionEntry = NamedTuple(
'FashionEntry',
  [
    ('id', str),
    ('type', str),
    ('caption', str)
  ]
)


def mkdirs_safe(path: AnyStr):
  """Make necessary directories if a path does not exist."""
  try:
    os.makedirs(path)
  except OSError as e:
    if e.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else:
      raise e


def import_excel_as_dataframe(
    path: AnyStr
) -> Dict[str, pandas.DataFrame]:
  # sheet_name=None returns all sheets in a map of sheet_name:DataFrame
  return pandas.read_excel(path, sheet_name=None)


def dataframe_to_fashion_entries(datafame: DataFrame) -> List[FashionEntry]:
  fashion_entries = []
  for _, row in datafame.iterrows():
    if all(pandas.notnull(row.get(key, None))
           for key in ('ID', 'TYPE', 'CAPTION')):
      entry = FashionEntry(row['ID'], row['TYPE'], row['CAPTION'])
      fashion_entries.append(entry)
  return fashion_entries


def categorize_and_merge_image_path(
    category: str,
    image_path: Path,
    merged_image_paths: Dict[str, List[Path]]
) -> None:
  if not image_path.stem.endswith('S'):
    pass
  if image_path.stem.lower().startswith(category):
    if category not in merged_image_paths:
      merged_image_paths[category] = [image_path]
    else:
      merged_image_paths.setdefault('extra', []).append(image_path)


def get_image_paths(
    character: str,
    entry: FashionEntry,
    parent_image_directory: Path
) -> Dict[str, List[Path]]:
  categories = ('front', 'right', 'back', 'left')
  image_paths = {}
  entry_image_directory = (
      parent_image_directory / character.lower() / entry.type.lower() / entry.id.lower()
  )
  if not entry_image_directory.is_dir():
    return image_paths
  for image_path in entry_image_directory.iterdir():
    relative_path = Path(
      '../gfx/{}/{}/{}.gif'
      .format(character, entry.type, entry.id, image_path.name)
    )
    for category in categories:
      categorize_and_merge_image_path(
        category=category,
        image_path=relative_path,
        merged_image_paths=image_paths
      )
  return image_paths


def render_fashion_entry_html(
    character: str,
    fashion_entry: FashionEntry,
    image_paths: Dict[str, List[Path]]
) -> str:
  category_order = ('front', 'right', 'back', 'left', 'extra')
  sorted_image_paths = []
  for category in category_order:
    sorted_image_paths.extend(image_paths.get(category, []))
  template = Template(textwrap.dedent("""\
    <div class="item-content center windowBG">
      <h>{{ caption }}
          <br>
        <hr>
        {% for path in sorted_image_paths %}
        <img class="preview" src="{{ path }}"/>
        {% endfor %}
      </h>
    </div>
  """))
  return template.render(
    caption=fashion_entry.caption,
    sorted_image_paths=sorted_image_paths
  )
