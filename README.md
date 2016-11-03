# apod_fts
PostgreSQL full text search example

# Installing
`apod_fts` is a web-application written in Python using flask web-framework. To run this application
you need to install `Flask` and `psycopg2` Python packages.

It is necessary that PostgreSQL binaries are in PATH environment. To install all text search dictionaries and RUM index you can use scripts in script directory. Use the following commands

```
createdb apod
psql apod < scripts/apod.dump
chmod +x scripts/01-create-configuration.sh
scripts/01-create-configuration.sh
chmod +x scripts/02-create-rum.sh
scripts/02-create-rum.sh
```
