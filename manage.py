import datetime
import enum
import json
import os
import sys
from argparse import _StoreAction, REMAINDER
from pathlib import Path

from argcmdr import Local, LocalRoot, localmethod
from terminaltables import AsciiTable


ROOT_PATH = Path(__file__).parent.resolve()
SRC_PATH = ROOT_PATH / 'src'


def store_env_override(option_strings,
                       dest,
                       envvar,
                       nargs=None,
                       default=None,
                       type=None,
                       choices=None,
                       description=None,
                       help=None,
                       metavar=None):
    if envvar == '':
        raise ValueError("unsupported environment variable name", envvar)

    envvalue = os.getenv(envvar)

    if default is None:
        default_value = envvalue
    elif callable(default):
        default_value = default(envvalue)
    else:
        raise TypeError("unsupported default -- expected callable or None")

    if description and help:
        raise ValueError(
            "only specify help to override its optional generation from "
            "description -- not both"
        )
    elif description:
        if default_value:
            help = '{} (default {} envvar {}: {})'.format(
                description,
                'provided by' if default is None else 'derived from',
                envvar,
                default_value,
            )
        else:
            help = (f'{description} (required because '
                    f'envvar {envvar} is empty)')

    return _StoreAction(
        option_strings=option_strings,
        dest=dest,
        nargs=nargs,
        const=None,
        default=default_value,
        type=type,
        choices=choices,
        required=(not default_value),
        help=help,
        metavar=metavar,
    )


class Marketplace(LocalRoot):
    """marketplace app management"""


@Marketplace.register
class Build(Local):
    """build app container image"""

    def __init__(self, parser):
        parser.add_argument(
            '--repository-uri',
            action=store_env_override,
            envvar='IMAGE_REPOSITORY_URI',
            description='image repository URI',
        )
        parser.add_argument(
            '--repository-name',
            action=store_env_override,
            envvar='IMAGE_REPOSITORY_NAME',
            description='image repository name',
        )
        parser.add_argument(
            '-n', '--name',
            action=store_env_override,
            envvar='IMAGE_REPOSITORY_NAME',
            default=lambda envvalue: envvalue and f'{envvalue}:latest',
            description='image name:tag',
        )
        parser.add_argument(
            '--label',
            action='append',
            help='additional name/tags to label image; the first of these, '
                 'if any, is treated as the "version"',
        )
        parser.add_argument(
            '--target',
            choices=('development', 'production'),
            default='production',
            help="target environment (default: production)",
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
        return '/'.join((self.args.repository_uri, name))

    def prepare(self, args, parser):
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
            yield from self['deploy'].prepare(args, parser)

    @localmethod('-l', '--login', action='store_true', help="log in to AWS ECR")
    def push(self, args):
        """push latest image to registry"""
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

    class Deploy(Local):
        """deploy the latest image container to the cluster service"""

        class UpdateServiceColumns(str, enum.Enum):

            id = 'ID'
            status = 'Status'
            desiredCount = 'Desired'
            pendingCount = 'Pending'
            createdAt = 'Created'
            updatedAt = 'Updated'

            def __str__(self):
                return self.value.__str__()

            def get_string(self, data):
                value = data[self.name]

                if self is self.createdAt or self is self.updatedAt:
                    return datetime.datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')

                return str(value)

        def __init__(self, parser):
            parser.add_argument(
                '--cluster',
                action=store_env_override,
                envvar='ECS_CLUSTER_NAME',
                description="short name or full Amazon Resource Name (ARN) "
                            "of the cluster that your service is running on",
            )
            parser.add_argument(
                '--service',
                action=store_env_override,
                envvar='ECS_SERVICE_NAME',
                description="name of the service to update",
            )
            parser.add_argument(
                '--no-quiet',
                action='store_true',
                default=False,
                dest='foreground',
                help="print command output",
            )
            parser.add_argument(
                '-qq',
                action='store_false',
                default=True,
                dest='report',
                help="do not print deployment result",
            )

        def prepare(self, args, parser):
            (_retcode, stdout, _stderr) = yield self.local['aws'][
                'ecs',
                'update-service',
                '--force-new-deployment',
                '--cluster', args.cluster,
                '--service', args.service,
            ]

            if getattr(args, 'report', True) and stdout is not None:
                try:
                    result = json.loads(stdout)

                    service_name = result['service']['serviceName']
                    deployments = result['service']['deployments']

                    data = [self.UpdateServiceColumns]
                    data.extend(
                        [
                            column.get_string(deployment)
                            for column in self.UpdateServiceColumns
                        ]
                        for deployment in deployments
                    )
                except (KeyError, ValueError):
                    print('unexpected command output:', stdout, file=sys.stderr, sep='\n')
                else:
                    table = AsciiTable(data, title=f"{service_name} deployments")
                    print(table.table)


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
