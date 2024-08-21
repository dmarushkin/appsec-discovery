# Appsec Discovery

It loads projects and open MRs from private Gitlab api, clone main branches and MRs code into local folders, extract db, proto, graphql schemas and client objects from code with semgrep rules, score it with rules, those you add via simple UI, normalize and put scored objects into service db and alert about critical changes in Telegram.

# Why we need all that

As Appsec specialist you can monitor your codebase for critical changes and review them manualy, also you can sum scores for particular fields and get overall risk score for entire projects, and use it for prioritization of any kind of appsec rutines (triage vulns, plan security audits).

As Governance, Risk, and Compliance (GRC) specialist you can use discovered data schemas for any kind of data governance (localize PII, payment and other critical data, dataflows), restricting access to and between critical services, focus on hardening environments that contain .

As Monitoring or Incident Response specialist you can focus you attention on logs and anomalies in critical services or even particular routes in your clients trafic.

As infra security specialist you can use same approach to extract structured data about your assets from IaC repositories like terraform or ansible (service now extracts VMs from terraform files).

# Logic schema

![Logic schema](https://github.com/dmarushkin/appsec-discovery/blob/main/discovery.png?raw=true)

# Concept

For extract data from code used simple semgrep rules:

![semgrep](https://github.com/dmarushkin/appsec-discovery/blob/main/semgrep.png?raw=true)

Objects extracted from metavars in json report:

![extract](https://github.com/dmarushkin/appsec-discovery/blob/main/extract.png?raw=true)

And stored in postgres database for analysis:

Protobuf:

![proto](https://github.com/dmarushkin/appsec-discovery/blob/main/proto.png?raw=true)

Table:

![db](https://github.com/dmarushkin/appsec-discovery/blob/main/db.png?raw=true)

External client:

![client](https://github.com/dmarushkin/appsec-discovery/blob/main/client.png?raw=true)




# Run service

First off all you need instansce of Gitlab with you product codebase, make service account with audit role and make personal api token.

Fillout .env file with your gitlab url and token, change passwords for local db and ui user, for alerts register new telegram bot or use exist one.

To run service localy you just need docker compose and run this command in project folder.

```
docker-compose up --build
```

For prod environments feel free to bake Docker images in your k8s env, use external db, production Grafana or Superset for dashboards and any kind off analytics ;)

