# Урок 0. Пустой проект и GitHub

## Цель

Публичный репозиторий `dashulya-study` на GitHub с окружением Python 3.12 через
`uv`, установленным AG2 и всеми файлами плана. В конце занятия `uv run` отрабатывает,
а `.env` не попадает в Git.

## Теория

- **`uv`** — быстрый менеджер Python и зависимостей. Проект описывается в
  `pyproject.toml`, версия Python фиксируется в `.python-version`, точные версии
  зависимостей — в `uv.lock`. Подробнее: <https://docs.astral.sh/uv/>.
- **`pyproject.toml`** — единственный файл, где объявлены зависимости проекта.
  `uv add <пакет>` дописывает туда зависимость и ставит её.
- **`.env`** — файл с секретами (ключи, токены), живёт только локально и не
  коммитится. **`.env.example`** — шаблон без секретов, который коммитится,
  чтобы любой видел, какие переменные нужны.
- **`.gitignore`** — список файлов, которые Git не должен отслеживать.
- **AG2** — фреймворк для агентов. Устанавливается как `ag2[openai]`; мы будем
  подключаться к Ollama Cloud через его OpenAI-совместимый API.

## Задание

Выполни на своём Mac, по порядку.

### 1. Установи uv

Через Homebrew:

```bash
brew install uv
```

Или без Homebrew:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Проверь: `uv --version`.

### 2. Создай репозиторий на GitHub

На [github.com/new](https://github.com/new):

- имя `dashulya-study`;
- **Public**;
- галочку «Add a README file» **не ставь** — создаём пустой репозиторий;
- `.gitignore` и лицензию пока не выбирай (файлы мы добавим сами).

### 3. Собери проект локально

```bash
mkdir -p ~/projects && cd ~/projects
git clone git@github.com:<твой-логин>/dashulya-study.git
cd dashulya-study
```

Внутри пустого репозитория:

```bash
uv init --app          # создаст main.py, pyproject.toml, .gitignore, README.md
uv python pin 3.12     # зафиксирует Python 3.12
uv add "ag2[openai]" python-dotenv
```

### 4. Добавь файлы плана

Скопируй из рабочей папки BB (или по одному) в корень репозитория:

- `README.md` (замени сгенерированный)
- `LICENSE` (замени `<your name>` на своё имя)
- `.gitignore` (замени сгенерированный, либо слей в один)
- `.env.example`
- `SPEC.md`
- `ROADMAP.md`
- `AGENTS.md`
- `PROGRESS.md`
- папку `lessons/` целиком

### 5. Создай .env

```bash
cp .env.example .env
```

Открой `.env` и впиши свой `OLLAMA_API_KEY` (с <https://ollama.com/settings/keys>).
`AG2_MODEL` пока оставь как есть — модель выберем на шаге 1.

### 6. Проверь окружение

```bash
uv run python -c "import ag2; print(ag2.__version__)"
```

Должна вывестись версия AG2 без ошибок.

### 7. Закоммить и отправь

```bash
git add .
git status          # убедись, что .env НЕ в списке
git commit -m "шаг 0: пустой проект, окружение и план обучения"
git push -u origin main
```

## Критерии готовности

- [ ] `uv run python -c "import ag2; print(ag2.__version__)"` выводит версию без ошибок.
- [ ] `git status` не показывает `.env`; `.env` отсутствует на GitHub.
- [ ] Репозиторий публичный, на `main` есть README, LICENSE, SPEC, ROADMAP,
      AGENTS, PROGRESS, `.env.example`, `.gitignore` и `lessons/`.
- [ ] Есть первый коммит.

## Подсказки (читай по одной, только если застрял)

1. `uv init` не хочет работать в непустой папке → можно запустить `uv init --app .`
   в корне репозитория.
2. `uv python pin 3.12` не находит версию → `uv python install 3.12`, затем повтори.
3. Не пушится по SSH → проверь `ssh -T git@github.com`; если не работает,
   настрой SSH-ключ по <https://docs.github.com/en/authentication/connecting-to-github-with-ssh>.
4. Сомневаешься, что `.gitignore` правильный → `git status --ignored` покажет
   игнорируемые файлы; `.env` должен быть среди них.

## Проверка

Пришли наставнику ссылку на репозиторий и вывод команды из пункта 6. После
проверки наставник выдаст урок 1 — первого агента.
