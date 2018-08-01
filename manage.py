import os
from argparse import REMAINDER
from pathlib import Path

from argcmdr import Local, LocalRoot, localmethod


ROOT_PATH = Path(__file__).parent.resolve()
SRC_PATH = ROOT_PATH / 'src'

IMAGE_REPOSITORY_NAME_DEFAULT = os.getenv('IMAGE_REPOSITORY_NAME')
IMAGE_REPOSITORY_URI_DEFAULT = os.getenv('IMAGE_REPOSITORY_URI')


def add_default(text, default):
    return f'{text} (default: {default})' if default else text


class Marketplace(LocalRoot):
    """marketplace app management"""


@Marketplace.register
class Build(Local):
    """build app container image"""

    def __init__(self, parser):
        default_name = IMAGE_REPOSITORY_NAME_DEFAULT and (IMAGE_REPOSITORY_NAME_DEFAULT + ':latest')

        parser.add_argument(
            '--repository-uri',
            default=IMAGE_REPOSITORY_URI_DEFAULT,
            help=add_default('Image repository URI',
                             IMAGE_REPOSITORY_URI_DEFAULT),
        )
        parser.add_argument(
            '--repository-name',
            default=IMAGE_REPOSITORY_NAME_DEFAULT,
            help=add_default('Image repository name',
                             IMAGE_REPOSITORY_NAME_DEFAULT),
        )
        parser.add_argument(
            '-n', '--name',
            default=default_name,
            help=add_default('Image name:tag', default_name),
        )
        parser.add_argument(
            '--label',
            action='append',
            help='Additional name/tags to label image; the first of these, '
                 'if any, is treated as the "version"',
        )
        parser.add_argument(
            '--target',
            choices=('development', 'production'),
            default='production',
            help="Target environment (default: production)",
        )
        parser.add_argument(
            '-l', '--login',
            action='store_true',
            help="log in to AWS ECR",
        )
        parser.add_argument(
            '-p', '--push',
            action='store_true',
            help="push image once built",
        )
        parser.add_argument(
            '-d', '--deploy',
            action='store_true',
            help="deploy the container once the image is pushed",
        )

    def get_full_name(self, name):
        if not self.args.repository_uri:
            self.args.__parser__.error(
                "image repository URI required "
                "(specify argument --repository-uri or "
                "environment variable IMAGE_REPOSITORY_URI)"
            )

        return '/'.join((self.args.repository_uri, name))

    def prepare(self, args, parser):
        dynamically_missing = [
            argument_descriptor for (argument_descriptor, argument_value) in (
                ('-n/--name', args.name),
                ('--repository-name', args.repository_name),
            ) if not argument_value
        ]
        if dynamically_missing:
            parser.error(
                "the following argument values could not be dynamically determined: " +
                ', '.join(dynamically_missing)
            )

        if args.login and not args.push:
            parser.error("will not log in outside of push operation")

        command = self.local['docker'][
            'build',
            '--build-arg', f'TARGET={args.target}',
            '-t', args.name,
            '-t', self.get_full_name(args.name),
        ]

        if args.label:
            for label in args.label:
                name = args.repository_name + ':' + label
                command = command[
                    '-t', name,
                    '-t', self.get_full_name(name),
                ]

        yield command[ROOT_PATH]

        if args.push:
            yield from self['push'].prepare(args)

        if args.deploy:
            yield self['deploy'].prepare(args)

    @localmethod('-l', '--login', action='store_true', help="log in to AWS ECR")
    def push(self, args):
        """push already-built image to registry"""
        if args.login:
            login_command = self.local['aws'][
                'ecr',
                'get-login',
                '--no-include-email',
                '--region', 'us-west-2',
            ]
            if args.show_commands or not args.execute_commands:
                print('>', login_command)
            if args.execute_commands:
                full_command = login_command()
                (executable, *arguments) = full_command.split()
                assert executable == 'docker'
                yield self.local[executable][arguments]

        yield self.local['docker'][
            'push',
            self.get_full_name(args.name),
        ]

    @localmethod
    def deploy(self, args):
        """deploy an image container"""
        # FIXME
        raise NotImplementedError

        command = self.local['eb']['deploy']

        # specify environment
        if args.target == 'production':
            command = command['appy-reviews-pro']
        else:
            command = command['appy-reviews-dev']

        if args.label:
            return command['-l', args.label[0]]
        return command


@Marketplace.register
class Develop(Local):
    """build, run and manage a Docker development container"""

    DEFAULT_NAMETAG = 'marketplace_web'

    @classmethod
    def run(cls, *args, name=None, **kwargs):
        docker = cls.local['docker']
        return docker[
            'run',
            '-p', '8000:8000',
            '-v', f'{SRC_PATH}:/app',
            '--env-file', str(ROOT_PATH / '.env'),
        ].bound_command(
            *args
        ).bound_command(
            *(
                f'-e{key}' if value is None else f'-e{key}={value}'
                for (key, value) in kwargs.items()
            )
        )[name or cls.DEFAULT_NAMETAG]

    def __init__(self, parser):
        super().__init__(parser)

        parser.add_argument(
            '-n', '--name',
            default=self.DEFAULT_NAMETAG,
            help=f'Image name/tag (default: {self.DEFAULT_NAMETAG})',
        )
        parser.add_argument(
            '-b', '--build',
            action='store_true',
            help="(re-)build image before container creation",
        )

    def exec(self, user='webapp', interactive=True, tty=True):
        command = self.local['docker']['exec']

        if user:
            command = command['-u', user]

        if interactive:
            command = command['-i']

        if tty:
            command = command['-t']

        return command[self.args.name]

    def prepare(self, args):
        if args.build:
            yield self.local['docker'][
                'build',
                '--build-arg', 'TARGET=development',
                '-t', args.name,
                ROOT_PATH,
            ]

        try:
            yield self.local['docker'][
                'stop',
                args.name,
            ]
        except self.local.ProcessExecutionError:
            pass
        else:
            yield self.local['docker'][
                'rm',
                args.name,
            ]

        yield self.run(
            '-d',
            '--name', args.name,
        )

    @localmethod('cmd', metavar='command', nargs=REMAINDER, help="shell command (default: bash)")
    @localmethod('--root', action='store_true', help="execute command as root")
    def shell(self, args):
        """execute a command -- by default a Bash shell -- in a running container"""
        kwargs = {'user': None} if args.root else {}
        yield (
            # foreground command to fully support shell
            self.local.FG(retcode=None),
            self.exec(**kwargs)[args.cmd or 'bash'],
        )

    @localmethod('mcmd', metavar='command', help="django management command")
    @localmethod('remainder', metavar='command arguments', nargs=REMAINDER)
    def djmanage(self, args):
        """manage the django project in a running container"""
        yield (
            # foreground command to fully support shell
            self.local.FG(retcode=None),
            self.exec()[
                './manage.py',
                args.mcmd,
                args.remainder,
            ],
        )


@Marketplace.register
class Db(Local):
    """manage the app database

    assuming a PostgreSQL target

    """
    class User(Local):

        user_flags = (
            '--encrypted',
            '--login',
            '--no-createdb',
            '--no-createrole',
            '--no-inherit',
            '--no-replication',
            '--no-superuser',
            '--echo',
            '--interactive',
            '--pwprompt',
        )

        default_database = 'marketplace'
        default_username = 'marketplace_webapp'

        @localmethod('name', nargs='?', default=default_username,
                     help=add_default("database user name", default_username))
        @localmethod('-g', '--group', action='append', dest='groups',
                     help='group(s)/role(s) to which to add user')
        @localmethod('-d', '--database', default=default_database,
                     help=add_default("database to which user is given access",
                                      default_database))
        def create(self, args):
            """create a database log-in for the webapp"""
            createuser = self.local['createuser'][self.user_flags]
            for group in args.groups or ():
                createuser = createuser['-g', group]

            yield createuser[args.name]

            yield self.local['psql'] << f'''
                grant connect on database {args.database} to {args.name};
            '''
