# Broken Link Report

**Name:** Broken Link Report  
**About:** Report a broken href from EPUB logs  
**Title:** `[Broken Link]`  
**Labels:** `bug`  

---

## Log Snippet

_Paste the relevant log lines from `epub_link_check_*.log`_

```yaml
- type: textarea
  id: log-snippet
  attributes:
  label: Log Snippet
  description: epub_link_check_*.log
  validations:
  required: true
```

---

## Affected File

_e.g., `chap_5.xhtml`_

```yaml
- type: input
  id: affected-file
  attributes:
  label: Affected File
  description: e.g., chap_5.xhtml
```
