# marketplace


# Deployment

## Run the web app

### Build docker image

From the project root run
```
docker build -t dssgmkt .
```
### Run the docker image

The app needs a set of environment variables to run - these are mandatory, the web app will not run without them.

The easiest way to provide the variables is to use one of the environment variables:

```
docker run -p 8000:8000 --env-file .env dssgmkt
```

The file .env.example contains a list of the variables needed; you can use that file as a base for your configuration.

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

You need to tell the app to collect the static assets (images, css, js, etc.) so that the web app can find them:
```
python manage.py collectstatic
```

Finally, restart webapp so it can read the static file changes:
```
supervisorctl restart webapp
```
