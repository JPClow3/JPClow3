# Contributing

Obrigado por considerar contribuir.

## Como contribuir

1. Faça um fork do repositório.
2. Crie uma branch para sua alteração:

   ```bash
   git checkout -b feat/minha-melhoria
   ```

3. Faça commits claros e pequenos.
4. Abra um Pull Request descrevendo:
   - objetivo da mudança
   - impacto visual/técnico
   - prints/GIF quando aplicável

## Qualidade mínima

- README consistente e sem links quebrados.
- Linguagem clara (PT-BR ou EN, mas consistente).
- Evitar segredos/credenciais em commits.

## Validação local (ambiente restrito)

Se o ambiente bloquear instalação de dependências externas
(ex.: `npm`/`apt` com erro 403), rode o lint offline:

```bash
python scripts/lint_markdown_offline.py
```

Esse fallback valida o essencial deste repositório, incluindo
HTML inline em Markdown (equivalente ao erro `MD033`).

## Lint oficial no GitHub Actions

O repositório também executa o lint oficial em PRs e pushes,
via workflow `.github/workflows/markdownlint.yml`.

- Local (fallback sem dependências externas):

  ```bash
  python scripts/lint_markdown_offline.py
  ```

- Remoto (oficial):
  `DavidAnson/markdownlint-cli2-action@v18`.
