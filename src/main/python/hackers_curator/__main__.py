import click

from .fashion_files import fashion_files


@click.group()
def main():
  """
  Hackers Curator command-line utility. For usage information on a
  particular subcommand, use --help after the name of the command.

  Example: hackers_curator fashion_files --help
  """
  pass


# Add subcommands
main.add_command(fashion_files)

# Entry point
main(prog_name='hackers_curator')
