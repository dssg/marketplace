# marketplace


# Deployment

## Run the web app

### Build a docker image

From the project root run
```
docker build -t dssgsolve .
```
### Run the docker image

The app needs a set of environment variables to run - these are mandatory, the web app will not run without them.

The easiest way to provide the variables is to use an env file:

```
docker run -p 8000:8000 --env-file .env dssgsolve
```

The provided file .env.example contains a list of the variables needed; you can use that file as a base for your configuration.

## First time setup

After the container is started, you need to do some first time setup before using the site.

If you run the commands below from outside the Docker container using `docker exec`, remember to run them as the user webapp:

```
docker exec -it <container_id> su webapp -c '<my_command>'
```

### DB initialization

First, do a Django database migration:
```
python manage.py migrate
```

Second, create a superuser, if needed access to the admin interface (remember to use your own values for username, password and email):
```
python manage.py create_superuser_cli --username test1 --password 123321 --noinput --email "blank@email.com"
```

Third, load the list of skills into the database:
```
python manage.py init_skills
```

### Static assets collection

You need to tell the app to collect the static assets (images, css, js, etc.) so that the web app can find them.
If you want to run the web app with DEBUG=False, you need to use AWS S3 as the backend for static and user-uploaded
files. The .env.example file contains a list of parameters that must be specified for using the S3 backend; those
properties need to be set before calling the collectstatic operation, as that command will copy static files to
the S3 bucket.

```
python manage.py collectstatic
```

Finally, restart the webapp so it can read the static file changes:
```
supervisorctl restart webapp
```

Your site should be available now at `localhost:8000`.
