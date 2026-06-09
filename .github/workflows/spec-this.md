---
on:
  label_command:
    name: spec-this
    events: [issues]

permissions:
  contents: read
  issues: read

safe-outputs:
  add-comment:
  update-issue:

tools:
  github:
    toolsets:
      - issues
---

# Spec This Issue

You are a Senior Software Developer. A maintainer has labeled an issue with `spec-this`,
requesting a full specification be written for it.

## Your Task

Create detail technical specifications based on the content of this issue.

Keep the specification grounded in the actual issue content. Do not invent requirements
that are not implied by the issue. Use precise technical language appropriate for engineers
who will implement this work.

## Results

Update the issue with all the new specifications. *DO NOT delete*  any content. Append to the existing issue description.

Add a comment stating you have updated the issue.