# Documentation

- Go to `localhost:80/docs` for swagger api documentation

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
PAGE_SIZE: int = 15
CACHE_CAPACITY_EMAIL_ID_LIST: int = 5
CACHE_CAPACITY_EMAIL_MODEL_LIST: int = 5
ENVIRONMENT: Literal['local', 'dev', 'prod'] = 'local'
```
