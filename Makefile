.PHONY: setup test train db-init run producer processor dashboard clean

PYTHON := py -3.11

setup:
	$(PYTHON) -m pip install -r requirements.txt
	$(PYTHON) scripts/download_dataset.py

db-init:
	$(PYTHON) database/db_initializer.py

train:
	$(PYTHON) ml/train_model.py

test:
	$(PYTHON) -m pytest -v

processor:
	$(PYTHON) processor/stream_processor.py

producer:
	$(PYTHON) producer/kafka_producer.py

dashboard:
	$(PYTHON) -m streamlit run app/dashboard.py

run:
	$(PYTHON) run_pipeline.py

clean:
	rm -rf __pycache__ */__pycache__ .pytest_cache
