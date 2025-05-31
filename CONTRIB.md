# CONTRIBUTING

Welcome — and thanks for taking the time to help improve the project!
This guide is intended to help you get started and outline the project's conventions.
Please read it carefully before contributing, or feed it to your favorite AI assistant so that it aligns with the project's design principles.

---

## 🚀 Quick Start

1. **Install dev dependencies**

   ```bash
   pip install -e '.[dev]"
   ```

2. **Format & lint**

   ```bash
   # Windows
   scripts\fmt.bat

   # macOS / Linux
   ./scripts/fmt.sh
   ```

3. **Run the tests**

   ```bash
   pytest
   ```

4. **Open a PR**
Make sure to associate your PR with an issue using `Fixes #<number>` in the description.

---

## 🎨 Code Style, Linting & Typing

| Category                             | Rule / Tool                       |
| ------------------------------------ | --------------------------------- |
| Base style                           | [PEP 8] + [PEP 257]               |
| Naming conventions                   | `snake_case` for functions & vars |
| `UPPER_CASE` for constants           |                                   |
| `CamelCase` for classes & exceptions |                                   |
| Prefix privates with `_`             |                                   |
| Line length                          | 120 chars                         |
| Formatting                           | `black .` (CI enforces)           |
| Import order                         | `isort .` (CI enforces)           |
| Static analysis                      | `flake8` (CI enforces)            |
| Type checking                        | Full [PEP 484] annotations        |
| Pass `mypy --strict`                 |                                   |

---

## 🧪 Tests

* Use **pytest** for all tests.
* Keep unit tests fast and deterministic.
* Aim for high coverage on new modules.

---


## 📦 Build & Release  (Maintainers Only)

### Local Build
One-liner: sets version, builds executables & wheels, uploads
<details>
<summary>Windows</summary>

```powershell
scripts\build_deploy_local.bat 0.1.0
```

</details>

<details>
<summary>macOS / Linux</summary>

```bash
./scripts/build_deploy_local.sh 0.1.0
```

</details>


### CI / GitHub Actions Release

1. **Tag & push**

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

2. **GitHub Release**
   Creating a release from the tag triggers the workflow that builds and uploads the package (with the version derived from the tag).

### Versioning

* Versions are derived by **setuptools-scm** from git tags
* No need to modify `__version__` strings

---

Thanks for contributing! 🙌

[PEP 8]: https://peps.python.org/pep-0008/
[PEP 257]: https://peps.python.org/pep-0257/
[PEP 484]: https://peps.python.org/pep-0484/
