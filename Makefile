# Arguments to pass to pytest on `make test`
PYTEST_ARGS ?= -m 'not selenium'
# poetry run command (it is prefixed to all python related commands).
POETRY ?= poetry run

### END CONFIG ###
.PHONY = clean all reset help initdb
.EXPORT_ALL_VARIABLES:

MANAGEPY = $(POETRY) python demo_project/manage.py
# CURRENT_BRANCH := $(shell git rev-parse --abbrev-ref HEAD)

# Help command,
# Idea from: https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

shell: ## ./manage.py shell
	cd demo_project && \
		$(MANAGEPY) shell

clean:  ## Cleanup your environment (deletes site_media/* !!)
	find . -name '__pycache__' -o -name '*.py[cod]' -exec rm {} \;
	rm -rf _build/*
	mkdir _build/site_media
	mkdir _build/staticfiles

resetdb:  ## Reset local database (dropdb, createdb, migrate, ...)
	rm -f _build/demo_db.sqlite3
	$(MANAGEPY) migrate

reset: clean resetdb  ## Reset all: db, media, redis, ...
	echo "DB and media reset"

demo: reset
	$(MANAGEPY) createdemo

test:  ## Run the test suite
	$(POETRY) pytest ${PYTEST_ARGS} --cov=vprad --cov-report=html:_build/coverage


