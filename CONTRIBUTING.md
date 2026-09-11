# Contributing to Formicx

Thank you for your interest in contributing to **Formicx**! Formicx is an open-source, agent-native runtime and control plane built for Linux environments.

We welcome contributions of all kinds: bug fixes, new features, documentation improvements, agent templates, and feedback.

---

## 1. Code of Conduct

Please be respectful, constructive, and inclusive in all interactions within the Formicx community.

---

## 2. Getting Started & Development Setup

### Prerequisites
- **Python 3.11+**
- **Git**
- **Linux or Windows** (Development is supported cross-platform; Linux/Raspberry Pi are primary deployment targets).

### Setting Up Your Local Environment

1. **Fork and Clone the Repository**
   ```bash
   git clone https://github.com/YOUR-USERNAME/Formicx.git
   cd Formicx
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Formicx in Editable Mode with Dev Dependencies**
   ```bash
   pip install -e .[dev]
   ```

4. **Run Automated Tests**
   ```bash
   pytest
   ```
   Ensure all 150+ tests pass before making changes.

---

## 3. Finding a Good First Issue

If you are new to Formicx or open-source contribution:
1. Check the [Good First Issues Guide](docs/GOOD_FIRST_ISSUES.md) or look for issues labeled [`good first issue`](https://github.com/Abbilaash/Formicx/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22) on GitHub.
2. Comment on the issue to let the community know you are working on it.

---

## 4. Development Workflow

1. **Create a Feature Branch**
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make Your Changes**
   Follow existing code formatting, add docstrings, and write unit tests for your changes.

3. **Run Verification & Tests**
   ```bash
   pytest
   ```

4. **Commit and Push**
   Use descriptive commit messages following Conventional Commits (e.g., `feat(cli): add --json flag`, `fix(daemon): handle timeout safely`).
   ```bash
   git add .
   git commit -m "feat(module): describe your change"
   git push origin feat/your-feature-name
   ```

5. **Open a Pull Request**
   Go to GitHub and create a Pull Request against `main`. Provide a summary of your changes and reference any related issues.

---

## 5. Architectural Overview

- **`src/formicx/core/`**: Domain models, runtime state, process management, local message bus, networking, discovery, policies.
- **`src/formicx/resources/`**: Process telemetry and `psutil` sampling monitor.
- **`src/formicx/daemon/`**: Daemon REST API control plane (`formicxd`).
- **`src/formicx/cli/`**: Typer-based CLI (`formicx agent ...`).
- **`src/formicx/sdk/`**: Developer SDK for agent implementation.
- **`tests/`**: Pytest test suite covering unit and integration scenarios.

---

## 6. Questions & Community

If you need help or have questions, feel free to open a [GitHub Discussion](https://github.com/Abbilaash/Formicx/discussions) or issue. Happy coding!
