# Validation Notes

Validated against a greenfield project shape with:

```text
app/
components/
db/migrations/
db/queries/
lib/
server/actions/
server/services/
tests/
```

The template gives Claude Code enough context to answer the first implementation step without asking for missing architecture decisions:

- where routes, server actions, services, queries, and migrations belong
- which commands to run
- how to name components, actions, query helpers, and tables
- how to handle SQLite migrations, transactions, indexes, and foreign keys
- what anti-patterns to avoid and why

Smoke prompt used:

```text
Create a workspace invitation flow with a database migration, query helpers,
server action, and dashboard form.
```

Expected interpretation from the template:

- migration goes under `db/migrations/`
- SQL access goes under `db/queries/`
- business rules and authorization go under `server/services/`
- the server action stays thin under `server/actions/`
- the dashboard form is a client component only for interaction state
