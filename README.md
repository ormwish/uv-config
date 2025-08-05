# uv-config

CLI-инструмент для работы с секцией `[tool.uv]` в `pyproject.toml`  
Использует Pydantic для валидации и Dynaconf для merge YAML/JSON/TOML  

## Особенности

- Валидация конфигурации `[tool.uv]`  
- Генерация шаблона с default-значениями  
- Merge defaults + пользовательский YAML/JSON ➔ `pyproject.toml`  
- Интерактивная установка/изменение параметров  
- Вывод справки по любому параметру  
- Комплект single-file Pydantic-моделей  

## Установка

```bash
uv pip install uv-config
```

или из Git:

```bash
uv pip install git+ssh://[email protected]/username/uv-config.git
```

## Быстрый старт

### Создать шаблон `pyproject.toml`

```bash
uv-config init
```

Сгенерирует:

```toml
[tool.uv]
package = true
resolution = "highest"
```

### Проверить конфигурацию

```bash
uv-config validate pyproject.toml
```

### Merge YAML ➔ TOML

```bash
uv-config merge pyproject.yaml
```

При наличии:

```yaml
tool:
  uv:
    managed: false
    sources:
      httpx:
        git: https://github.com/encode/httpx
        tag: 0.27.0
```

получим обновлённый `pyproject.toml`.

### Установить параметр

```bash
uv-config set pyproject.toml prerelease allow
```

### Справка по параметру

```bash
uv-config param resolution
```

Выведет тип, возможные значения и описание.

## Интеграция с uv

Добавьте в свой `pyproject.toml`:

```toml
[project.optional-dependencies]
uv = ["uv-config"]

[project.entry-points.uv.external]
config = "uv_config.cli:app"
```

После установки `uv pip install .[uv]` команда станет доступна как:

```bash
uv config validate pyproject.toml
```

## Разработка

1. Клонировать репозиторий  
2. Установить dev-зависимости  
   ```bash
   uv pip install -e .[dev]
   ```
3. Запустить тесты и линтинг  
   ```bash
   pytest
   flake8 uv_config
   ```

## Лицензия

[MIT License](LICENSE)