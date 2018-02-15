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
@click.option('--image-links-relative-path',
              help='Relative path to images folder for hyperlinks.',
              default='../../../gfx/fashion')
@click.option('--output-directory',
              help='Path to fashion files output directory.',
              type=click.Path(file_okay=False,
                              writable=True),
              required=True)
def fashion_files(
    excel_path: AnyStr,
    images_directory: AnyStr,
    image_links_relative_path: AnyStr,
    output_directory: AnyStr
) -> None:
  dataframes = import_excel_as_dataframe(pathify(excel_path))
  for (character, dataframe) in dataframes.items():
    fashion_entries = dataframe_to_fashion_entries(dataframe)
    character_path = Path(output_directory).expanduser() / character.capitalize()
    Path.mkdir(character_path, parents=True, exist_ok=True)
    for entry in fashion_entries:
      entry_image_paths = get_image_paths(
        character=character,
        entry=entry,
        image_links_relative_path=image_links_relative_path,
        parent_image_directory=Path(images_directory).expanduser()
      )
      html = render_fashion_entry_html(
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


def pathify(path_str: AnyStr) -> Path:
  return Path(path_str).expanduser()


def import_excel_as_dataframe(path: Path) -> Dict[str, pandas.DataFrame]:
  # sheet_name=None returns all sheets in a map of sheet_name:DataFrame
  return pandas.read_excel(str(path), sheet_name=None)


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
  if (image_path.stem.lower().startswith(category)
      and image_path.stem.endswith('S')):
    if category not in merged_image_paths:
      merged_image_paths[category] = [image_path]
    else:
      merged_image_paths.setdefault('extra', []).append(image_path)


def get_image_paths(
    character: str,
    entry: FashionEntry,
    image_links_relative_path: str,
    parent_image_directory: Path
) -> Dict[str, List[Path]]:
  categories = ('front', 'right', 'back', 'left')
  image_paths = {}
  entry_image_directory = (parent_image_directory / character.lower() /
                           entry.type.lower() / entry.id.lower())
  if not entry_image_directory.is_dir():
    return image_paths
  for image_path in entry_image_directory.iterdir():
    relative_path = (Path(image_links_relative_path) / character.lower() /
                     entry.type.lower() / entry.id.lower() / image_path.name)
    for category in categories:
      categorize_and_merge_image_path(
        category=category,
        image_path=relative_path,
        merged_image_paths=image_paths
      )
  return image_paths


def render_fashion_entry_html(
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
        <hr>{% for path in sorted_image_paths %}
        <img class="preview" src="{{ path }}"/>{% endfor %}
      </h>
    </div>
  """))
  return template.render(
    caption=fashion_entry.caption,
    sorted_image_paths=sorted_image_paths
  )
