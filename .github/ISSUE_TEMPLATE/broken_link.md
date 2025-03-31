name: Broken Link Report
about: Report a broken href from EPUB logs
title: "[Broken Link] "
labels: bug
body:
  - type: textarea
    id: log-snippet
    attributes:
      label: Log Snippet
      description: Paste the relevant log lines from epub_link_check_*.log
    validations:
      required: true
  - type: input
    id: affected-file
    attributes:
      label: Affected File
      description: e.g., chap_5.xhtml
