BUILD_DIR=build

clean:
	@rm -rf $(BUILD_DIR)


prepare:
	git clone https://github.com/Netflix/bless.git $(BUILD_DIR)
	cd $(BUILD_DIR) && virtualenv venv && . venv/bin/activate && make develop && make test
	mkdir $(BUILD_DIR)/lambda_configs


build:
	cd $(BUILD_DIR) && virtualenv venv && . venv/bin/activate && pip install --upgrade pip setuptools && pip install -e .
	if [ -d  $(BUILD_DIR)/venv/lib/python2.7/site-packages ]; then \
		cp -r $(BUILD_DIR)/venv/lib/python2.7/site-packages/. $(BUILD_DIR)/aws_lambda_libs; \
	fi
	if [ -d  $(BUILD_DIR)/venv/lib64/python2.7/site-packages ]; then \
		cp -r $(BUILD_DIR)/venv/lib64/python2.7/site-packages/. $(BUILD_DIR)/aws_lambda_libs; \
	fi

configure:
	@python configure.py --password $(shell < /dev/urandom tr -dc _A-Z-a-z-0-9 | head -c128)

publish:
	@cp lambda_handler.py $(BUILD_DIR)/aws_lambda_libs
	@chmod 0666 $(BUILD_DIR)/lambda_configs/ca.pem
	@chmod 0666 $(BUILD_DIR)/lambda_configs/ca.pem.pub
	@cd $(BUILD_DIR) && virtualenv venv && . venv/bin/activate && make develop && make publish
	@chmod 0600 $(BUILD_DIR)/lambda_configs/ca.pem
	@chmod 0600 $(BUILD_DIR)/lambda_configs/ca.pem.pub
	@echo "Zip file located at $(BUILD_DIR)/publish/bless_lambda.zip"
	@echo "Don't forget to run make clean once you have deployed the zip, the CA private key is still in the build dir"

all: clean prepare build configure publish


.PHONY: prepare clean build configure publish all