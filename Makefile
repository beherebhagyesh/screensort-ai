.PHONY: help install run run-ai run-full test lint clean docker docker-run

# Default target
help:
	@echo "ScreenSort AI - Available commands:"
	@echo ""
	@echo "  make install     Install Python dependencies"
	@echo "  make install-ai  Install AI dependencies (Moondream2)"
	@echo "  make install-all Install all optional dependencies"
	@echo ""
	@echo "  make run         Run basic OCR mode"
	@echo "  make run-ai      Run with AI categorization"
	@echo "  make run-full    Run with all features (AI+OCR+Video+Translate)"
	@echo ""
	@echo "  make test        Run unit tests"
	@echo "  make lint        Run flake8 linter"
	@echo "  make clean       Remove cache files"
	@echo ""
	@echo "  make docker      Build Docker image"
	@echo "  make docker-run  Run in Docker container"

# Installation
install:
	pip install pytesseract Pillow pytest

install-ai: install
	pip install llama-cpp-python
	python download_model.py

install-video:
	pip install opencv-python

install-translate:
	pip install langdetect googletrans==4.0.0-rc1

install-all: install install-ai install-video install-translate
	@echo "All dependencies installed!"

# Running
run:
	python sort_screenshots.py --interval 60

run-ai:
	python sort_screenshots.py --ai --interval 60

run-full:
	python sort_screenshots.py --ai --ai-ocr --video --translate --interval 60

run-bg:
	nohup python sort_screenshots.py --ai --ai-ocr --translate > sort.log 2>&1 &
	@echo "Started in background. Check sort.log for output."

stop:
	pkill -f "python.*sort_screenshots.py" || echo "Not running"

# Development
test:
	pytest test_sort_screenshots.py -v

lint:
	flake8 sort_screenshots.py --max-line-length=120 --ignore=E501,W503

lint-fix:
	@echo "Note: Auto-fix not available. Please fix manually."
	flake8 sort_screenshots.py --max-line-length=120 --ignore=E501,W503

check: lint test
	@echo "All checks passed!"

# Cleanup
clean:
	rm -rf __pycache__ .pytest_cache *.pyc
	rm -f sort.log

clean-all: clean
	rm -f screenshots.db
	rm -rf knowledge_base

# Docker
docker:
	docker build -t screensort-ai .

docker-run:
	docker run -it --rm \
		-v $(PWD)/screenshots:/screenshots \
		-e SCREENSORT_AI=1 \
		screensort-ai --ai --interval 60

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down
