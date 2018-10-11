from django.core.management.base import BaseCommand
from django.template.loader import render_to_string


class Command(BaseCommand):

    help = (
        # FIXME: default setup of argparse squashes newlines, etc.
        "render an app template to standard output\n\n"
        "for example, to render the maintenance page, for use in production, "
        "(from a development environment), you might:\n\n"
        "\tAWS_STORAGE_BUCKET_NAME=solve.dssg.io DEFAULT_FILE_STORAGE=s3 "
        "./manage.py render 503-maintenance.html > ~/docs/503-maintenance.html"
    )

    def add_arguments(self, parser):
        parser.add_argument(
            'template_name',
            metavar='template',
            help="namespaced path to template to render (for example: "
                 "marketplace/about.html)",
        )
        parser.add_argument(
            '--var',
            action='append',
            dest='vars_',
            metavar='var',
            help="context variables to set, (only strings supported, "
                 "for example: user_type=volunteer)",
        )

    def handle(self, template_name, vars_, **options):
        self.stdout.write(
            render_to_string(
                template_name,
                vars_ and dict(var_spec.split('=') for var_spec in vars_),
            )
        )
