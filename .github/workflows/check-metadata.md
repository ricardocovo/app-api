---
on:
  schedule: daily
  workflow_dispatch:

permissions:
  contents: read
  issues: read

safe-outputs:  
  create-issue:
    title-prefix: "[Metadata Failure] "
    labels: [automation]
    max: 1
    close-older-issues: true
    deduplicate-by-title: 1

tools:
  github:
    toolsets:
      - issues
---

# Check Metadata

You are auditing the repository to ensure all metadata is present.

## Review

A file called "metadata.yml" should exist on the repo, with the following information:

```yml
appid: my-application-id
appname: My Application Name
owner:
  - team-lead@example.com
  - owner@example.com
tags:
  - platform
  - microservice
  - api
```

Definition:

- appid: formatted as`^[A-Z]{2}\d{4}$`
- appname: name with no spaces, no longer than 128 characters
- owners: list of emails, at least 2 required.
- tags: list of tags, at least 1 required

## Action

If the application does not have a `metadata.yml` file, or the file is incomplete, create an issue on the repo.

The issues title should include the date in the format "MMM DD, YYYY".

The description should include the failure description (either is missing, or does not comply - include the reason for non-compliance)