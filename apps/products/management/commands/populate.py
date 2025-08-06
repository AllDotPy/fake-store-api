from django.core.management.base import BaseCommand

from apps.utils.script import add_products

####
##      COMMAND CLASS
#####
class Command(BaseCommand):
    """Django command to populate the database with generic products"""

    help = "Populate database with generic products"

    def add_arguments(self, parser):
        """Add populate Comand arguments"""

        # NUMBER
        parser.add_argument(
            '-l', '--limit', type = int, default = 100,
            help = 'Nombre de produits à générer'
        )

    def handle(self, *args, **options):
        """Handle Populate command"""

        # Start generating
        self.stdout.write("Generating.....")

        # Generate products
        limit = options.get('limit')
        try:
            add_products(limit)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Generated {limit} Products successfully'
                )
            )
        except Exception as e:
             self.stdout.write(
                self.style.ERROR(
                    f'Error Generated {limit} Products: {e}'
                )
            )
