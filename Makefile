# For Python bindings ===========================================================

# Version of C2PA to use
C2PA_VERSION := $(shell cat c2pa-native-version.txt)

# Start from clean env: Delete `.venv`, then `python3 -m venv .venv`
# Pre-requisite: Python virtual environment is active (source .venv/bin/activate)
# Run Pytest tests in virtualenv: .venv/bin/pytest tests/test_unit_tests.py -v

# Removes build artifacts, distribution files, and other generated content
clean:
	rm -rf artifacts/ build/ dist/

# Performs a complete cleanup including uninstalling the c2pa package and clearing pip cache
clean-c2pa-env: clean
	python3 -m pip uninstall -y c2pa
	python3 -m pip cache purge

# Installs all required dependencies from requirements.txt and requirements-dev.txt
install-deps:
	python3 -m pip install -r requirements.txt
	python3 -m pip install -r requirements-dev.txt

# Installs the package in development mode (editable, requires cwd to be project root)
build-python:
	python3 -m pip install -e .

# Installs the package to system Python (non-editable, .so copied to site-packages)
install-python:
	python3 -m pip install .

# Performs a complete rebuild of the development environment
rebuild: clean-c2pa-env install-deps download-native-artifacts build-python
	@echo "Development rebuild done"

# Performs a complete install to system Python (usable from any directory, downloads prebuilt .so)
install: clean-c2pa-env install-deps download-native-artifacts install-python
	@echo "System install done"

# Performs a complete install using locally compiled .so (for GLIBC compatibility)
install-from-source: clean-c2pa-env install-deps build-native-from-source install-python
	@echo "System install (from source) done"

run-examples:
	python3 ./examples/sign.py
	python3 ./examples/sign_info.py
	python3 ./examples/training.py
	rm -rf output/

# Runs the examples, then the unit tests
test:
	make run-examples
	python3 ./tests/test_unit_tests.py
	python3 ./tests/test_unit_tests_threaded.py

# Runs benchmarks in the venv
benchmark:
	python3 -m pytest tests/benchmark.py -v

# Tests building and installing a local wheel package
# Downloads required artifacts, builds the wheel, installs it, and verifies the installation
test-local-wheel-build:
	# Clean any existing builds
	rm -rf build/ dist/
	# Download artifacts and place them where they should go
	python3 scripts/download_artifacts.py $(C2PA_VERSION)
	# Install Python
	python3 -m pip install -r requirements.txt
	python3 -m pip install -r requirements-dev.txt
	python3 -m build --wheel
	# Install local build in venv
	pip install $$(ls dist/*.whl)
	# Verify installation in local venv
	python3 -c "import c2pa; print('C2PA package installed at:', c2pa.__file__)"
	# Verify wheel structure
	twine check dist/*

# Tests building and installing a local source distribution package
# Downloads required artifacts, builds the sdist, installs it, and verifies the installation
test-local-sdist-build:
	# Clean any existing builds
	rm -rf build/ dist/
	# Download artifacts and place them where they should go
	python3 scripts/download_artifacts.py $(C2PA_VERSION)
	# Install Python
	python3 -m pip install -r requirements.txt
	python3 -m pip install -r requirements-dev.txt
	# Build sdist package
	python3 setup.py sdist
	# Install local build in venv
	pip install $$(ls dist/*.tar.gz)
	# Verify installation in local venv
	python3 -c "import c2pa; print('C2PA package installed at:', c2pa.__file__)"
	# Verify sdist structure
	twine check dist/*

# Verifies the wheel build process and checks the built package and its metadata
verify-wheel-build:
	rm -rf build/ dist/ src/*.egg-info/
	python3 -m build
	twine check dist/*

# Manually publishes the package to PyPI after creating a release
publish: release
	python3 -m pip install twine
	python3 -m twine upload dist/*

# Code analysis
check-format:
	python3 -m py_compile src/c2pa/c2pa.py
	flake8 src/c2pa/c2pa.py

# Formats Python source code using autopep8 with aggressive settings
format:
	autopep8 --aggressive --aggressive --in-place src/c2pa/c2pa.py

# Downloads the required native artifacts for the specified version
download-native-artifacts:
	python3 scripts/download_artifacts.py $(C2PA_VERSION)

# Platform-specific artifact directory
PLATFORM_ID := $(shell python3 -c "import platform; m={'x86_64':'x86_64-unknown-linux-gnu','aarch64':'aarch64-unknown-linux-gnu','AMD64':'x86_64-pc-windows-msvc','arm64':'aarch64-apple-darwin','x86_64_darwin':'x86_64-apple-darwin'}; a=platform.machine(); s=platform.system(); print(m.get(a+'_darwin',m.get(a,''))) if s=='Darwin' else print(m.get(a,''))")
C2PA_RS_DIR := /tmp/c2pa-rs

# 从 c2pa-rs 源码编译 libc2pa_c.so（解决 GLIBC 版本不兼容问题）
# 前置要求：需要 Rust 工具链 >= 1.86.0（可通过 make install-rust 安装）
build-native-from-source:
	@echo "=== 从源码编译 c2pa-c-ffi ($(C2PA_VERSION)) ==="
	@command -v cargo >/dev/null 2>&1 || { echo "错误: 未找到 cargo，请先运行 make install-rust"; exit 1; }
	@echo "Rust 版本: $$(rustc --version)"
	@echo "Cargo 版本: $$(cargo --version)"
	rm -rf $(C2PA_RS_DIR)
	git clone --branch $(C2PA_VERSION) --depth 1 https://github.com/contentauth/c2pa-rs.git $(C2PA_RS_DIR)
	cd $(C2PA_RS_DIR) && cargo build --release -p c2pa-c-ffi --features file_io,rust_native_crypto
	mkdir -p artifacts/$(PLATFORM_ID)
	cp $(C2PA_RS_DIR)/target/release/libc2pa_c.so artifacts/$(PLATFORM_ID)/libc2pa_c.so
	@echo "已复制 libc2pa_c.so 到 artifacts/$(PLATFORM_ID)/"
	ldd artifacts/$(PLATFORM_ID)/libc2pa_c.so
	@echo "=== 源码编译完成 ==="

# 安装/升级 Rust 工具链（通过 rustup）
install-rust:
	curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
	@echo "请运行: source $$HOME/.cargo/env 然后重新执行 make 命令"

# Build API documentation with Sphinx
docs:
	python3 scripts/generate_api_docs.py
