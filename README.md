# Appsec Discovery

Appsec Discovery service provide continuous assets and risk management based on Gitlab codebase. 

It scheduled fetching information about related code projects and open merge requests from Gitlab API, cloning related code into local folders, extraction from code structured database, protobuf, graphql schemas and used api clients and methods with semgrep rules, scoring risk level for gathered objects with provided rules, storing scored objects in service database for further analytics and corellations with other appsec data in Trino and Superset, alerting about new risky objects in code projects and critical changes on diff in via Telegram or merge request comments.

# Usage examples

 - Appsec specialists can monitor codebase for critical changes and review them manualy, also sum scores for particular fields and get overall risk score for entire projects, and use it for prioritization of any kind of appsec rutines (triage vulns, plan security audits).

 - Governance, Risk, and Compliance (GRC) specialists can use discovered data schemas for any kind of data governance (localize PII, payment and other critical data, dataflows), restricting access to and between critical services, focus on hardening environments that contain critical data.

 - Monitoring or Incident Response specialists can focus attention on logs and anomalies in critical services or even particular routes in clients traffic.

 - Infrastructure security specialists can use same approach to extract structured data about assets from IaC repositories like terraform or ansible (service now extracts VMs from terraform files).

# Logic schema

![Logic schema](https://github.com/dmarushkin/appsec-discovery/blob/main/discovery.png?raw=true)

Service components:

 - **discovery_scanner** scheduled background parallel tasks for fetching projects, MRs info and code from Gitlab, scanning with semgrep, scoring results, calculating diffs and sending alerts;

 - **discovery_ui** React Admin CRUD for managing scoring rules;

 - **discovery_api** FastAPI for scoring rules crud;

 - **discovery_nginx** router for React static js and api in one origin

 - **discovery_db** for storing code projects, branches, open mrs, scanning state and extracted objects

# Workflow

1. Appsec set risk scoring rules in discovery_ui, gitlab url, project prefixes and api token for scans, tg creds for alerts in env vars for discovery_scanner.
2. discovery_scanner fetch projects list for provided prefixes and add projects updated from last fetch to updateing branches and MRs queue.
3. discovery_scanner fetch info about updated branches and mrs and add new ones to clone code queue.
4. discovery_scanner clone code for main branches and source and target branches code for MRs, add successfully cloned to scan queue.
5. discovery_scanner extract assets objects, score risk for particular object fields, store objects into local database.
6. discovery_scanner calculate objects and fields diff for source and target branches in MRs, alert about new risky fields.
7. discovery_scanner clean code and scan results cache for processed tasks.
8. Appsec triage alerted changes in Telegram or Gitlab UIs.
9. Appsec connect discovery_db to analytics services like Grafana or Superset via Trino, setup business dashboards for vuln and risk prioritisation, thresholds and alerts

# Concept

For extract data from code used simple semgrep rules:

![semgrep](https://github.com/dmarushkin/appsec-discovery/blob/main/semgrep.png?raw=true)

Objects extracted from metavars in json report:

![extract](https://github.com/dmarushkin/appsec-discovery/blob/main/extract.png?raw=true)

And stored in postgres database for analysis:

![db](https://github.com/dmarushkin/appsec-discovery/blob/main/db.png?raw=true)

More about concept with examples in https://hackernoon.com/building-asset-and-risk-management-on-codebase-with-semgrep


# Run service

First off all you need instansce of Gitlab with you product codebase, make service account with audit role and make personal api token.

Fillout .env file with your gitlab url and token, change passwords for local db and ui user, for alerts register new telegram bot or use exist one.

To run service localy you just need docker compose and run this command in project folder.

```
docker-compose up --build
```

For prod environments feel free to bake Docker images in your k8s env, use external db, production Grafana or Superset for dashboards and any kind off analytics ;)

