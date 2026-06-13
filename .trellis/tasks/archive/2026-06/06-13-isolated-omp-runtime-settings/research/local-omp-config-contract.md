# Local OMP Config Contract

## Evidence

* `omp --help` for local `omp/15.10.8` documents `PI_CODING_AGENT_DIR` as the session storage directory defaulting to `~/.omp/agent`.
* OMP `src/config/settings.ts` constructs `config.yml` as `path.join(agentDir, "config.yml")`.
* OMP `src/config/model-registry.ts` constructs a `ModelsConfigFile` relocated to the configured models path and validates custom provider entries.
* OMP `src/config/models-config-schema.ts` accepts provider entries with `baseUrl`, `apiKey`, `api`, `auth`, `models`, and per-model `id`, `api`, `baseUrl`, `compat`, and related fields.
* OMP `src/sdk.ts` defaults `agentDir` from `getDefaultAgentDir()` and passes `agentDir` into settings, session manager, prompt/template discovery, skills discovery, and secrets loading.
* The user's current system OMP config file is `/home/vimalinx/.omp/agent/config.yml`, with hash `cc6e3f8d7b812867006f5b64c3c094f70c424d4409a6ab737b6aa6188066c4ec` before this task.

## Implications For GA-TUI

* The embedded OMP process must receive `PI_CODING_AGENT_DIR=<GA-TUI harness>/runtime/ohmypi/agent` through the child process environment.
* Generated OMP files should live under that isolated directory, especially `config.yml`, `models.yml`, sessions, and cache DB files.
* GA-TUI should not rely on `OPENAI_BASE_URL` to override OMP's bundled OpenAI provider; custom gateway use should be represented as a custom provider in isolated `models.yml`.
* GA-TUI can map OpenAI-compatible `/model` entries to OMP providers with `api: openai-completions` or `api: openai-responses`, `baseUrl`, `apiKey`, and a single model entry.
* A separate OMP runtime root keeps OMP source config, sessions, and any migrations from touching system `~/.omp/agent`.

## Suggested MVP Mapping

```yaml
# <harness>/runtime/ohmypi/agent/config.yml
modelRoles:
  default: ga-tui-openai-compatible/qwen3.5
providers:
  webSearch: tavily
memory:
  backend: local
todo:
  eager: true
browser:
  headless: true
autoResume: true
```

```yaml
# <harness>/runtime/ohmypi/agent/models.yml
providers:
  ga-tui-openai-compatible:
    baseUrl: https://api.example.invalid/v1
    apiKey: env:GA_TUI_OMP_API_KEY_<digest>
    api: openai-completions
    models:
      - id: qwen3.5
        api: openai-completions
```

The env indirection avoids writing API keys into generated model files if the current implementation can set per-process env vars.
