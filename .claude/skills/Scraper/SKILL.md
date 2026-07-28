```markdown
# Scraper Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches you the core development patterns used in the "Scraper" Python repository. You'll learn about its coding conventions, file organization, import/export styles, and how to write and run tests. While no specific frameworks or automated workflows were detected, this guide helps you follow the repository's established practices for consistent, maintainable code.

## Coding Conventions

### File Naming
- Use **camelCase** for file names.
  - Example: `dataFetcher.py`, `urlParser.py`

### Import Style
- Use **relative imports** within the project.
  - Example:
    ```python
    from .utils import parseHtml
    from .dataFetcher import fetchData
    ```

### Export Style
- Use **named exports** (explicitly define what is exported from a module).
  - Example:
    ```python
    def fetchData(url):
        # implementation
        pass

    def parseHtml(html):
        # implementation
        pass

    __all__ = ['fetchData', 'parseHtml']
    ```

### Commit Patterns
- Commit messages are freeform (no strict prefix), averaging 67 characters.
  - Example: `Fix bug in data extraction for nested tables`

## Workflows

### Adding a New Scraper Module
**Trigger:** When you need to add a new scraping functionality for a different website or data type.
**Command:** `/add-scraper-module`

1. Create a new Python file using camelCase (e.g., `newSiteScraper.py`).
2. Implement your scraping logic using relative imports for shared utilities.
3. Define your export functions and update `__all__` accordingly.
4. Write corresponding tests in a file named `newSiteScraper.test.py`.
5. Commit your changes with a descriptive message.

### Running Tests
**Trigger:** When you want to verify your code changes.
**Command:** `/run-tests`

1. Identify test files (pattern: `*.test.*`).
2. Use your preferred Python test runner (e.g., `pytest`, `unittest`) to execute tests.
   - Example:
     ```bash
     pytest newSiteScraper.test.py
     ```
3. Review the output and fix any failing tests.

### Refactoring Imports
**Trigger:** When reorganizing code or moving files.
**Command:** `/refactor-imports`

1. Update relative import paths in affected files.
2. Ensure all modules use relative imports for internal dependencies.
3. Run tests to confirm that imports resolve correctly.

## Testing Patterns

- Test files follow the pattern: `*.test.*` (e.g., `dataFetcher.test.py`).
- The specific testing framework is not enforced; use any Python test runner.
- Place test files alongside their respective modules or in a dedicated test directory.
- Example test structure:
  ```python
  from .dataFetcher import fetchData

  def test_fetchData_valid_url():
      result = fetchData('https://example.com')
      assert result is not None
  ```

## Commands
| Command              | Purpose                                             |
|----------------------|-----------------------------------------------------|
| /add-scraper-module  | Scaffold and add a new scraping module              |
| /run-tests           | Run all test files matching the `*.test.*` pattern  |
| /refactor-imports    | Update and verify relative imports after refactoring|
```
