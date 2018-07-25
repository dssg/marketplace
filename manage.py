from pathlib import Path

from argcmdr import Local, LocalRoot, localmethod


ROOT_PATH = Path(__file__).parent.resolve()
SRC_PATH = ROOT_PATH / 'src'


class Marketplace(LocalRoot):
    """marketplace app management"""


@Marketplace.register
class Build(Local):
    """build app container image"""

    DEFAULT_NAMETAG = 'dsapp/marketplace/web:{tag}'

    REGISTRY = '093198349272.dkr.ecr.us-west-2.amazonaws.com'

    default_name = DEFAULT_NAMETAG.format(tag='latest')

    @classmethod
    def get_full_name(cls, name):
        return '/'.join((cls.REGISTRY, name))

    def __init__(self, parser):
        parser.add_argument(
            '-n', '--name',
            default=self.default_name,
            help=f'Image name/tag (default: {self.default_name})',
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
                name = self.DEFAULT_NAMETAG.format(tag=label)
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

    def prepare(self, args):
        if args.build:
            yield self.local['docker'][
                'build',
                '--build-arg', 'TARGET=development',
                '-t', args.name,
                ROOT_PATH,
            ]

        yield self.run(
            '-d',
            '--name', args.name,
        )
