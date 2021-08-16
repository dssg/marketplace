# Solve for Good Platform
## Development

### Getting started

The DSSG Marketplace is built to run under Python v3.7. Virtual environment management is strongly recommended in development, using at least the [venv](https://docs.python.org/3/library/venv.html) module, or [pyenv](https://github.com/pyenv/pyenv).

Also note that the marketplace requires configuration, documented by example in [.env.example](.env.example). This configuration may be supplied as either process environment variables or via a file named `.env` added to the repository root directory. If neither are supplied the application will not start.

To quickly bootstrap your development environment, having cloned the repository, invoke the executable `develop` script from your system shell:

    ./develop

This wizard will initialize a local application configuration file (`.env`), and suggest set-up steps and optionally execute these, for example:

    (install) begin

    (pyenv) installed ✓

    (python-3.7.0) installed ✓

    (marketplace) installed ✓

    (lib) install?
    1) yes, install {pip install -r requirement/console.txt}
    2) no, ignore
    #? 1

The marketplace assumes a [Docker](https://www.docker.com/) image build target; and so, the Python requirements of the Web app are not themselves automatically installed into the project virtual environment.

If you'd like to build the app in your project virtual environment, you may:

    pip install -r requirement/development.txt

Regardless, ensure that `docker` is installed on your system.

### Build for development

To build the app's Docker image for local development:

    manage develop [-b/--build]

The above command will build an image of the app, with additional development utilities, and start a container of this image, with the local (host) `src/` directory mounted into the container, and using your local configuration (from `.env`).

To recreate this container without rebuilding, simply omit the `--build` argument.

### Local app management

To manage the app container through Docker, many commands must be of the form:

    docker exec [-u webapp] [-i] [-t] <container_id> <command> ...

…or via the management shortcut:

    manage develop shell [--root] [<command> ...]

The most common Web app commands are routed through Django, via `src/manage.py`, *e.g.*:

    ./src/manage.py migrate

…and so a management shortcut is provided to invoke Django commands from within the app container:

    manage develop djmanage <command> ...

### Local app intialization

Initialize and migrate the database:

    manage develop djmanage migrate

Load skills data:

    manage develop djmanage init_skills

Create a superuser:

    manage develop djmanage createsuperuser

And, so long as you are not using Django's `runserver` command along with its filesystem-based static asset backend, you'll have to "collect" these assets (images, css, js, *etc.*), and then restart the Web server:

    manage develop djmanage collectstatic

To restart the Web server:

    manage develop restart

(The equivalent of: `manage develop shell --root supervisorctl restart webapp`.)

The Web app binds to `localhost:8000`.

## Deployment

### Automation

The marketplace integrates with [GitHub Actions](https://github.com/dssg/marketplace/actions) for automated deployment via a [workflow named CI/CD](.github/workflows/build-deploy.yml).

The CI/CD workflow is triggered by the publishing of a [GitHub Release](https://github.com/dssg/marketplace/releases). Only releases for semantically-named tags are considered for deployment. Tags of the form `[0-9].[0-9].[0-9]` will be built and deployed to both staging and production. Tags of the form `[0-9].[0-9]*` will be deployed to staging only. Releases for tags of any other form are ignored.

The workflow executes the same `manage` commands as those outlined below for manual use.

**Note**: The automated workflow *will not* instruct the deployment target to collect static assets nor to migrate the database. These tasks may be performed manually following an automated deployment; or, it is advised that such deployments be performed manually in their entirety.

The below commands will, by default, [record the deployment with GitHub](https://api.github.com/repos/dssg/marketplace/deployments). Neither manual nor automated deployments against non-latest tags or already-deployed tags will succeed.

### Build for deployment

To build the app's Docker image for deployment:

    manage build [--label=LABEL] {staging,production}

It is recommended to provide a label, in the form of a version number, *e.g.*: `1.0.2`. This tag should also be applied to the Git repository.

### Configure deployment

The image repository name and base URI may be specified every time as arguments to `manage build`, or set in the process environment, under the names:

| Environment variable    | Build CLI argument  |
| --------------------    | ------------------  |
| `IMAGE_REPOSITORY_NAME` | `--repository-name` |
| `IMAGE_REPOSITORY_URI`  | `--repository-uri`  |

Some deployment commands moreover require Amazon Web Services (AWS) credentials, which must be set in the environment – either the pair, `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`, or simply `AWS_PROFILE`.

For a full accounting of environment variables relevant to deployment, consult [.envrc.example](.envrc.example).

### Push to repository

The latest deployment image may be pushed to the image repository via the build sub-command `push`:

    manage build {staging,production} push

Or a new image may be built and pushed in one command:

    manage build {staging,production} [-p/--push]

### Authentication

In order to push an image to the repository, you must have created an authenticated session. The `-l/--login` flag may be passed to both `build` and `build push`:

    manage build {staging,production} -lp

### Image promotion

To promote the latest pushed image to production, *i.e.* to deploy, invoke the build sub-command `deploy`:

    manage build {staging,production} deploy [--static] [--migrate]

Either flag `--static` or `--migrate` instructs the `deploy` command, after promoting the latest image, to **wait** for at least one Web server to start a container based on this image; and, subsequently, to instruct this container, via SSH, to execute either the `collectstatic` command, the `migrate` command, or both.

(**Note**: This wait can be significant, ~ 5 minutes. Moreover, this procedure is relatively fragile, and sensitive to, *e.g.*, overlapped deployments.)

Like other build subcommands, `deploy` may be rolled up into the build command:

    manage build {staging,production} [-p/--push] [-d/--deploy]

However, in this form, no deploy-specific options may be passed, (such as `--migrate`).
