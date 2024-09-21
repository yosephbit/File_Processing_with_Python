echo "\nStarting isort ..."
poetry run isort .

echo "\nStarting flake8 ..."
poetry run flake8

echo "\nStarting mypy ..."
poetry run mypy .

echo "Starting black ..."
poetry run black .
