# C2PA Python library

## 快速安装指南

提供三种安装方式，根据环境选择：

### 方式一：从 PyPI 安装（推荐，适用于大多数场景，但是要求Python 3.10+）

```bash
pip install c2pa-python
```

### 方式二：从 GitHub 下载预编译库安装（开发/部署）

```bash
# 下载预编译的 .so 并安装到系统 Python（任意目录可 import）
make install

# 或仅安装为开发模式（仅项目目录内可 import）
make rebuild
```

### 方式三：从源码编译安装（解决 GLIBC 版本不兼容问题）

当 Docker 容器或服务器的 GLIBC 版本较低（如 GLIBC 2.28），导致预编译的 `.so` 无法加载时（报错 `GLIBC_2.32 not found`），需要从源码编译：

```bash
# 1. 安装 Rust 工具链（如已安装可跳过）
make install-rust
source $HOME/.cargo/env

# 2. 一键从源码编译 .so 并安装到系统 Python
make install-from-source
```

> **说明**：`make install-from-source` 会自动从 [c2pa-rs](https://github.com/contentauth/c2pa-rs) 克隆源码、编译 `libc2pa_c.so`，并将其安装到系统 `site-packages`，在任意目录下均可 `import c2pa`。

### Make 命令速查

| 命令 | 说明 |
|------|------|
| `make install` | 下载预编译 `.so` + 正式安装到系统 Python |
| `make install-from-source` | 从源码编译 `.so` + 正式安装到系统 Python |
| `make rebuild` | 下载预编译 `.so` + 开发模式安装（仅项目目录可用） |
| `make install-rust` | 安装/升级 Rust 工具链 |
| `make build-native-from-source` | 仅从源码编译 `.so`（不执行 Python 安装） |
| `make test` | 运行示例和单元测试 |
| `make clean` | 清理构建产物 |

---

The [c2pa-python](https://github.com/contentauth/c2pa-python) repository provides a Python library that can:

- Read and validate C2PA manifest data from media files in supported formats.
- Create and sign manifest data, and attach it to media files in supported formats.

Features:

- Create and sign C2PA manifests using various signing algorithms.
- Verify C2PA manifests and extract metadata.
- Add assertions and ingredients to assets.
- Examples and unit tests to demonstrate usage.

<div style={{display: 'none'}}>

For the best experience, read the docs on the [CAI Open Source SDK documentation website](https://opensource.contentauthenticity.org/docs/c2pa-c).

If you want to view the documentation in GitHub, see:
- [Using the Python library](docs/usage.md)
- [Supported formats](https://github.com/contentauth/c2pa-rs/blob/main/docs/supported-formats.md)
- [Configuring the SDK using `Context` and `Settings`](docs/context-settings.md)
- [Using Builder intents](docs/intents.md) to ensure spec-compliant manifests
- Using [working stores and archvies](docs/working-stores.md)
- Selectively constructing manifests by [filtering actions and ingredients](docs/selective-manifests.md)
- [Diagram of public classes in the Python library and their relationships](docs/class-diagram.md)
- [Release notes](docs/release-notes.md)

</div>

## Prerequisites

This library requires Python version 3.10+.

## Package installation

Install the c2pa-python package from PyPI by running:

```bash
pip install c2pa-python
```

To use the module in Python code, import the module like this:

```python
import c2pa
```

## Examples

See the [`examples` directory](https://github.com/contentauth/c2pa-python/tree/main/examples) for some helpful examples:

- `examples/read.py` shows how to read and verify an asset with a C2PA manifest.
- `examples/sign.py` shows how to sign and verify an asset with a C2PA manifest.
- `examples/training.py` demonstrates how to add a "Do Not Train" assertion to an asset and verify it.

## API reference documentation

Documentation is published at [github.io/c2pa-python/api/c2pa](https://contentauth.github.io/c2pa-python/api/c2pa/index.html).

To build documentation locally, refer to [this section in Contributing to the project](https://github.com/contentauth/c2pa-python/blob/main/docs/project-contributions.md#api-reference-documentation).

## Contributing

Contributions are welcome!  For more information, see [Contributing to the project](https://github.com/contentauth/c2pa-python/blob/main/docs/project-contributions.md).

## License

This project is licensed under the Apache License 2.0 and the MIT License. See the [LICENSE-MIT](https://github.com/contentauth/c2pa-python/blob/main/LICENSE-MIT) and [LICENSE-APACHE](https://github.com/contentauth/c2pa-python/blob/main/LICENSE-APACHE) files for details.
