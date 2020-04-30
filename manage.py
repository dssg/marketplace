import datetime
import enum
import itertools
import json
import os
import re
import sys
import textwrap
import time
from argparse import _StoreAction, REMAINDER
from pathlib import Path

from argcmdr import Local, LocalRoot, localmethod
from terminaltables import AsciiTable


ROOT_PATH = Path(__file__).parent.resolve()
SRC_PATH = ROOT_PATH / 'src'


def spincycle(chars='|/–\\', file=sys.stdout, wait=1):
    """A generator which writes a "spinner" to file, cycling through
    the given characters, with the given wait between writes.

    The last written character is yielded to the iterator, such that a
    polling procedure may be executed with the given wait, while the
    file (stdout) is updated.

    """
    for char in itertools.cycle(chars):
        file.write(char)
        file.flush()

        yield char

        time.sleep(wait)
        file.write('\b')


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
    """Construct an argparse action which stores the value of a command
    line option to override a corresponding value in the process
    environment.

    If the environment variable is not empty, then no override is
    required. If the environment variable is empty, and no default is
    provided, then the "option" is required.

    In the case of a default value which is a *transformation* of the
    single environment variable, this default may be provided as a
    callable, (*e.g.* as a lambda function).

    Rather than have to fully explain the relationship of this
    environment-backed option, help text may be generated from a
    provided description.

    """
    if envvar == '':
        raise ValueError("unsupported environment variable name", envvar)

    envvalue = os.getenv(envvar)

    if callable(default):
        default_value = default(envvalue)
    elif envvalue:
        default_value = envvalue
    else:
        default_value = default

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


class ContainerRegistryMixin:

    def __init__(self, parser):
        super().__init__(parser)

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


class Marketplace(LocalRoot):
    """marketplace app management"""


@Marketplace.register
class Build(ContainerRegistryMixin, Local):
    """build app container image"""

    def __init__(self, parser):
        super().__init__(parser)

        parser.add_argument(
            '-n', '--name',
            help='image name:tag (default derived from repository name: '
                 '{REPOSITORY_NAME}:latest)',
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
        parser.add_argument(
            '-f', '--force',
            dest='show_warnings',
            action='store_false',
            default=True,
            help="ignore warnings",
        )

    def get_full_name(self, name):
        return '/'.join((self.args.repository_uri, name))

    def prepare(self, args, parser):
        if args.login and not args.push:
            parser.error("will not log in outside of push operation")

        repository_latest = args.repository_name + ':latest'
        command = self.local['docker'][
            'build',
            '--build-arg', f'TARGET={args.target}',
            '-t', (args.name or repository_latest),
            '-t', self.get_full_name(repository_latest),
        ]

        if args.label:
            for label in args.label:
                name = args.repository_name + ':' + label
                command = command[
                    '-t', name,
                    '-t', self.get_full_name(name),
                ]
        elif args.show_warnings and args.target == 'production':
            parser.error(textwrap.dedent("""\
                at least the standard versioning label is recommended for builds intended for production

                for example – 0.1.1 –

                    manage build --label 0.1.1

                ensure that you have pulled the latest from the Git repository, and consult –

                    git tag -l --sort version:refname

                – for the tags currently in use. and, ensure that you apply (and push) the same tag
                to the source in the Git repository as to the Docker image here, for example –

                    git tag -a 0.1.1

                (to suppress this warning, see: `manage build --force`)\
                """))

        yield command[ROOT_PATH]

        if args.push:
            yield from self['push'].delegate()

        if args.deploy:
            yield from self['deploy'].delegate()

    @localmethod('-l', '--login', action='store_true', help="log in to AWS ECR")
    def push(self, args):
        """push image(s) to registry"""
        if args.login:
            login_command = self.local['aws'][
                'ecr',
                'get-login',
                '--no-include-email',
                '--region', 'us-west-2',
            ]
            self.print_command(login_command)
            if args.execute_commands:
                full_command = login_command()
                (executable, *arguments) = full_command.split()
                assert executable == 'docker'
                yield self.local[executable][arguments]

        yield self.local['docker'][
            'push',
            self.get_full_name(args.repository_name),
        ]

    class Deploy(Local):
        """deploy the latest image container to the cluster service"""

        TASK_START_PATTERN = re.compile(r'\(service (?P<service_name>[\w-]+)\) '
                                        r'has started (?P<number_tasks>\d+) '
                                        r'tasks: \(task (?P<task_id>[\w-]+)\)\.')

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
                '--static',
                action='store_true',
                help="collect and deploy static assets upon deployment",
            )
            parser.add_argument(
                '--migrate',
                action='store_true',
                help="migrate the database upon deployment",
            )

            parser.add_argument(
                '--ssh',
                action=store_env_override,
                default='ssh',
                envvar='ECS_SSH',
                metavar='COMMAND',
                description='ssh command through which to execute post-deployment tasks',
            )

            # Note: This override only works when command is called
            # outright, not when delegated:
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

        def prepare(self, args, parser, local):
            last_event = None
            if args.static or args.migrate:
                # AWS CLI and ECS CLI provide no great way of tying deployments
                # to containers and instances, which makes this quite annoying.
                #
                # Retrieve a baseline event:
                (_retcode, stdout, _stderr) = yield local['aws'][
                    'ecs',
                    'describe-services',
                    '--cluster', args.cluster,
                    '--services', args.service,
                ]
                if stdout is not None:
                    result = json.loads(stdout)
                    (service,) = result['services']
                    last_event = service['events'][0]

            # update service (deploy)
            (_retcode, stdout, _stderr) = yield local['aws'][
                'ecs',
                'update-service',
                '--force-new-deployment',
                '--cluster', args.cluster,
                '--service', args.service,
            ]

            # report on deployments
            if args.report and stdout is not None:
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

            # post-deployment actions
            if last_event:
                # there are post-deployment actions and this is not a dry run
                #
                # poll event stream to discover newly-started task reflecting
                # deployed version
                spinner = spincycle(['']) if args.show_commands else spincycle()
                for _cycle in spinner:
                    (_retcode, stdout, _stderr) = yield local['aws'][
                        'ecs',
                        'describe-services',
                        '--cluster', args.cluster,
                        '--services', args.service,
                    ]
                    result = json.loads(stdout)
                    (service,) = result['services']
                    events = tuple(itertools.takewhile(
                        lambda event: event['id'] != last_event['id'],
                        service['events']
                    ))
                    for event in reversed(events):
                        task_start_match = self.TASK_START_PATTERN.match(event['message'])
                        if task_start_match:
                            task_id = task_start_match.group('task_id')
                            break
                    else:
                        # no match -- skip cycle
                        continue

                    # match found -- break loop
                    print('\b')
                    break

                # trace task to its EC2 instance
                # (AWS CLI you are terrible)
                (_retcode, stdout, _stderr) = yield local['aws'][
                    'ecs',
                    'describe-tasks',
                    '--cluster', args.cluster,
                    '--tasks', task_id,
                ]
                result = json.loads(stdout)
                (task,) = result['tasks']

                (_retcode, stdout, _stderr) = yield local['aws'][
                    'ecs',
                    'describe-container-instances',
                    '--cluster', args.cluster,
                    '--container-instances', task['containerInstanceArn'],
                ]
                result = json.loads(stdout)
                (container_instance,) = result['containerInstances']

                (_retcode, stdout, _stderr) = yield local['aws'][
                    'ec2',
                    'describe-instances',
                    '--instance-ids', container_instance['ec2InstanceId'],
                ]
                result = json.loads(stdout)
                (ec2_reservation,) = result['Reservations']
                (ec2_instance,) = ec2_reservation['Instances']
                public_ip = ec2_instance['PublicIpAddress']

                (ssh_exec, *ssh_args) = args.ssh.split()
                ssh = local[ssh_exec].bound_command(*ssh_args)[public_ip]

                image_path = '/'.join((args.repository_uri, args.repository_name))
                for _cycle in spinner:
                    # FIXME: We've seen it not here tho it should be: investigate
                    (_retcode, stdout, _stderr) = yield ssh['docker'][
                        'ps',
                        '--filter', f'ancestor={image_path}',
                        '--format', '"{{.Names}}"',
                    ]
                    try:
                        (container_name,) = stdout.splitlines()
                    except ValueError:
                        continue
                    else:
                        print('\b')
                        break

                container = ssh['docker']['exec', '-u', 'webapp', container_name]

                if args.migrate:
                    yield (
                        local.FG(retcode=None),
                        container['./manage.py', 'migrate']
                    )

                if args.static:
                    yield (
                        local.FG(retcode=None),
                        container['./manage.py', 'collectstatic', '--no-input', '-v', '1']
                    )


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

    def exec(self, user='webapp', interactive=True, tty=True, **environ):
        command = self.local['docker']['exec']

        if user:
            command = command['-u', user]

        if interactive:
            command = command['-i']

        if tty:
            command = command['-t']

        if environ:
            command = command[[
                ('--env', f'{key}={value}') for (key, value) in environ.items()
            ]]

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

    @localmethod
    def restart(self):
        """restart the web server"""
        yield self.exec(user=None, interactive=False, tty=False)[
            'supervisorctl',
            'restart',
            'webapp',
        ]

    @localmethod('remainder', metavar='command arguments', nargs=REMAINDER)
    @localmethod('mcmd', metavar='command', help="django management command")
    @localmethod('-e', '--env', action='append', help='set environment variables')
    def djmanage(self, args):
        """manage the django project in a running container"""
        yield (
            # foreground command to fully support shell
            self.local.FG(retcode=None),
            self.exec(
                PAGER='more',
                **dict(pair.split('=') for pair in args.env or ()),
            )[
                './manage.py',
                args.mcmd,
                args.remainder,
            ],
        )
