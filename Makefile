# SAMPLE DATABASES
DB_NAME = pagila
DB_USER = postgres
DB_PASSWORD = password
DB_HOST = localhost
DB_PORT = 5432
DB_IMAGE = pagila_postgres

# Default target: Generate the sample database
.PHONY: all start-db stop-db cleanup generate-pagila-db cleanup-pagila-db help

# Build and run the Pagila database
generate-pagila-db:
	@echo "Building and running Pagila database..."
	docker build -t $(DB_IMAGE) example_databases/pagila
	docker run --name $(DB_NAME) -e POSTGRES_USER=${DB_USER} -e POSTGRES_PASSWORD=$(DB_PASSWORD) -d -p $(DB_PORT):5432 $(DB_IMAGE)

# Stop and delete the Pagila database
cleanup-pagila-db:
	@echo "Stopping and removing Pagila database..."
	docker stop $(DB_NAME) && docker rm $(DB_NAME)

# Display available Makefile commands
help:
	@echo "Available Makefile commands:"
	@echo ""
	@echo "  make generate-pagila-db       - Build and run Pagila database"
	@echo "  make cleanup-pagila-db        - Stop and delete Pagila database"
	@echo "  make help                    - Show this help message"
