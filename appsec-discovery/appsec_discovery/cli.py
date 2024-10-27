import click
from appsec_discovery import some_function

@click.command()
@click.option('--name', default='world', help='Name to greet')
def main(name):
    """Простой пример команды приветствия."""
    result = some_function(name)
    click.echo(f"Hello, {result}!")

if __name__ == '__main__':
    main()
