# Bank Service

Модель банка: счета, клиенты, транзакции, аудит рисков и отчёты.

## Запуск

```bash
python -m scr.main
```

Демо создаёт банк, клиентов, пачку операций и сразу пишет отчёты с графиками.

## Куда смотреть результат

**Отчёты** — папка `reports/` в корне проекта:

- по клиенту: `client_olga.json` и CSV в `reports/client_olga/`
- по банку: CSV в `reports/bank/`
- по рискам: `risks.json` и CSV в `reports/risk/`

**Графики** — `reports/charts/`:

- `bar_chart.png` — балансы клиентов
- `pie_chart.png` — доли балансов
- `change_balance.png` — изменение баланса по транзакциям
