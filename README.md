# Documentation

- Go to `localhost:8001/docs` for swagger api documentation
## Example
http://localhost:8001/inbox?start_date=2024-01-01&end_date=2024-01-31&subject=google

# Configuration
## Commands
```sh
# run locally
docker-compose up --build
```

## Environment Variables
```sh
# .env
EMAIL_PASSWORD=***
EMAIL_USER=demo@gmail.com

# These can be set in the config.py and .env
# Can also be set in the environment of any dockerfile
PAGE_SIZE: int = 15
CACHE_CAPACITY_EMAIL_ID_LIST: int = 5
CACHE_CAPACITY_EMAIL_MODEL_LIST: int = 5
ENVIRONMENT: Literal['local', 'dev', 'prod'] = 'local'
```
