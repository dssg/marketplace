import datetime
import dateutil.parser
import enum
import functools
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
from descriptors import cachedclassproperty
from plumbum.commands import ExecutionModifier
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


class EnvDefault(str):
    pass


def store_env_override(option_strings,
                       dest,
                       envvar,
                       nargs=None,
                       default=None,
                       type=None,
                       choices=None,
                       description=None,
                       addendum=None,
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
    provided description. (And an addendum may be optionally appended to
    the end of the generated text.)

    To aide in the differentiation of whether the resulting value
    originated from the command line or the process environment, the
    environment-derived default (and its optional transformation) are
    wrapped in the ``str`` subclass: ``EnvDefault``.

    """
    if envvar == '':
        raise ValueError("unsupported environment variable name", envvar)

    envvalue = os.getenv(envvar)

    if callable(default):
        default_value = EnvDefault(default(envvalue))
    elif envvalue:
        default_value = EnvDefault(envvalue)
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
            if addendum:
                help += f' {addendum}'
        else:
            help = (f'{description} (required because '
                    f'envvar {envvar} is empty)')
    elif addendum:
        raise ValueError("addendum intended for use in conjunction with description")

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


class _SHH(ExecutionModifier):
    """plumbum execution modifier to ensure output is not echoed to terminal

    essentially a no-op, this may be used to override argcmdr settings
    and cli flags controlling this feature, on a line-by-line basis, to
    hide unnecessary or problematic (e.g. highly verbose) command output.

    """
    __slots__ = ('retcode', 'timeout')

    def __init__(self, retcode=0, timeout=None):
        self.retcode = retcode
        self.timeout = timeout

    def __rand__(self, cmd):
        return cmd.run(retcode=self.retcode, timeout=self.timeout)


SHH = _SHH()


class EnvironmentMixin:

    def __init__(self, parser):
        super().__init__(parser)

        parser.add_argument(
            'target',
            choices=('staging', 'production',),
            help="target environment",
        )


class ClusterServiceMixin:

    environmental = False

    @cachedclassproperty
    def _environmental(cls):
        return cls.environmental or issubclass(cls, EnvironmentMixin)

    def __init__(self, parser):
        super().__init__(parser)

        parser.add_argument(
            '--cluster',
            action=store_env_override,
            envvar='ECS_CLUSTER_NAME',
            description="short name or full Amazon Resource Name (ARN) "
		        "of the cluster that your service is running on",
            addendum='(default extended for staging with suffix: -staging)'
                     if self._environmental else None,
        )
        parser.add_argument(
            '--service',
            action=store_env_override,
            envvar='ECS_SERVICE_NAME',
            description="name of the service to update",
            addendum='(default extended for staging with suffix: -staging)'
                     if self._environmental else None,
        )

        parser.set_defaults(
            resolve_cluster=functools.lru_cache()(self.resolve_cluster),
            resolve_service=functools.lru_cache()(self.resolve_service),
        )

    def resolve_cluster(self):
        if (
            self._environmental and
            self.args.target == 'staging' and
            isinstance(self.args.cluster, EnvDefault)
        ):
            return self.args.cluster + '-staging'

        return self.args.cluster

    def resolve_service(self):
        if (
            self._environmental and
            self.args.target == 'staging' and
            isinstance(self.args.service, EnvDefault)
        ):
            return self.args.service + '-staging'

        return self.args.service

    def describe_service(self, suppress=True):
        modifier = SHH if suppress else None
        (_retcode, stdout, _stderr) = yield modifier, self.local['aws'][
            'ecs',
            'describe-services',
            '--cluster', self.args.resolve_cluster(),
            '--services', self.args.resolve_service(),
        ]

        if stdout is None:
            return None

        result = json.loads(stdout)
        (service,) = result['services']
        return service


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
            addendum='(default extended for staging to: …/staging)'
                     if isinstance(self, EnvironmentMixin) else None,
        )
        parser.set_defaults(
            resolve_repository_name=functools.lru_cache()(self.resolve_repository_name),
        )

    def resolve_repository_name(self):
        if (
            isinstance(self, EnvironmentMixin) and
            self.args.target == 'staging' and
            isinstance(self.args.repository_name, EnvDefault)
        ):
            return self.args.repository_name + '/staging'

        return self.args.repository_name


class Marketplace(LocalRoot):
    """marketplace app management"""


@Marketplace.register
class Db(Local):
    """manage databases"""

    default_production_id = 'marketplace-db'
    default_staging_id = 'marketplace-staging-db'

    @localmethod('--name', default=default_staging_id,
                 help=f"database instance name to apply (default: {default_staging_id})")
    @localmethod('--from', dest='from_name', metavar='NAME', default=default_production_id,
                 help=f"database instance whose snapshot to use (production) "
                      f"(default: {default_production_id})")
    def build_staging(self, args, parser):
        """restore most recent production snapshot to NEW staging database"""
        # Look up production instance info (vpc subnet group, etc.)
        (_retcode, stdout, _stderr) = yield SHH, self.local['aws'][
            'rds',
            'describe-db-instances',
            '--db-instance-identifier',
            args.from_name,
        ]

        if stdout is None:
            subnet_group_name = 'DRY-RUN'
        else:
            try:
                (description,) = json.loads(stdout)['DBInstances']
                subnet_group_name = description['DBSubnetGroup']['DBSubnetGroupName']
            except (KeyError, TypeError, ValueError):
                print(stdout)
                raise ValueError('unexpected response')

        def snapshot_datetime(data):
            timestamp = data['SnapshotCreateTime']
            return dateutil.parser.parse(timestamp)

        (_retcode, stdout, _stderr) = yield SHH, self.local['aws'][
            'rds',
            'describe-db-snapshots',
            '--snapshot-type', 'automated',
            '--db-instance-identifier', args.from_name,
        ]

        if stdout is None:
            snapshot_id = 'DRY-RUN'
        else:
            try:
                snapshots = json.loads(stdout)['DBSnapshots']
                snapshots_available = (snapshot for snapshot in snapshots
                                       if snapshot['Status'] == 'available')
                snapshots_sorted = sorted(snapshots_available, key=snapshot_datetime, reverse=True)
                snapshot_id = snapshots_sorted[0]['DBSnapshotIdentifier']
            except IndexError:
                parser.error(f"{args.from_name} has no snapshots available")
            except (KeyError, TypeError, ValueError):
                print(stdout)
                raise ValueError('unexpected response')

        yield self.local['aws'][
            'rds',
            'restore-db-instance-from-db-snapshot',
            '--no-publicly-accessible',
            '--db-subnet-group-name', subnet_group_name,
            '--db-instance-identifier', args.name,
            '--db-snapshot-identifier', snapshot_id,
        ]

    build_staging.__name__ = 'build-staging'


@Marketplace.register
class Build(ContainerRegistryMixin, EnvironmentMixin, Local):
    """build app container image for deployment"""

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
            '-f', '--force',
            dest='show_warnings',
            action='store_false',
            default=True,
            help="ignore warnings",
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

        repository_tag = args.name or (args.resolve_repository_name() + ':latest')
        command = self.local['docker'][
            'build',
            '--build-arg', 'TARGET=production',
            '-t', repository_tag,
            '-t', self.get_full_name(repository_tag),
        ]

        if args.label:
            for label in args.label:
                name = args.resolve_repository_name() + ':' + label
                command = command[
                    '-t', name,
                    '-t', self.get_full_name(name),
                ]
        elif args.show_warnings and args.target == 'production':
            parser.error(textwrap.dedent("""\
                at least the standard versioning label is recommended for builds intended for production

                for example – 0.1.1 –

                    manage build --label 0.1.1 production

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
            self.get_full_name(args.resolve_repository_name()),
        ]

    class Deploy(ClusterServiceMixin, Local):
        """deploy the latest image container to the cluster service"""

        environmental = True  # flag for ClusterServiceMixin

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
            super().__init__(parser)

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
                service = yield from self.describe_service(suppress=False)
                if service is not None:
                    last_event = service['events'][0]

            # update service (deploy)
            modifier = SHH if args.__command__ is not self else None
            (_retcode, stdout, _stderr) = yield modifier, local['aws'][
                'ecs',
                'update-service',
                '--force-new-deployment',
                '--cluster', args.resolve_cluster(),
                '--service', args.resolve_service(),
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
                    service = yield from self.describe_service(suppress=False)
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
                    '--cluster', args.resolve_cluster(),
                    '--tasks', task_id,
                ]
                result = json.loads(stdout)
                (task,) = result['tasks']

                (_retcode, stdout, _stderr) = yield local['aws'][
                    'ecs',
                    'describe-container-instances',
                    '--cluster', args.resolve_cluster(),
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

                image_path = '/'.join((args.repository_uri, args.resolve_repository_name()))
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

                # Grab target environment's entrypoint
                #
                # NOTE: This might change; but currently, the Dockerfile leaves
                # the default entrypoint, and sets the default command to
                # supervisor/webapp. However, *in staging/production*, the
                # entrypoint is set to `chamber`, to populate
                # configuration/secrets.
                #
                # We'll set our own command here to execute, of course; but, it
                # won't succeed without reinstituting the target environment's
                # entrypoint, (which `exec` won't do for us).
                #
                # (It's conceivable that this could be resolved by baking
                # `chamber` into the Dockerfile entrypoint, with a null backend
                # when environment not established by the environ. But,
                # investigation is warranted.)
                #
                # Rather than build the logic of that entrypoint here, we'll
                # simply read it from the running container, and prepend it to
                # our command.

                (_retcode, stdout, _stderr) = yield ssh['docker'][
                    'inspect',
                    '--format', '"{{json .Config.Entrypoint}}"',
                    container_name,
                ]
                entrypoint = json.loads(stdout)
                container = container[entrypoint]

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
