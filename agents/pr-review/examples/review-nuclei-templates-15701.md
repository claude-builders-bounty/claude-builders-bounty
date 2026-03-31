## PR Review: Add 5 KEV CVE templates (Pulse Secure, Cisco IP Phone, SAP CRM)

### Summary
This PR adds 10 new nuclei vulnerability detection templates for CISA Known Exploited Vulnerabilities (KEV), targeting Pulse Secure/Ivanti VPN appliances, Cisco IP Phones, SAP CRM, Telerik UI, Array Networks, Apache Struts, and Cisco IOS XE. All templates use detection-only matchers without exploitation payloads, following the repository's safe-scan convention. The changes are purely additive (+674 lines, 0 deletions) across 10 new YAML files organized by CVE year.

### Risk Assessment
- **False positive risk in CVE-2017-9248** (`http/cves/2017/CVE-2017-9248.yaml`): The matcher checks for `"Index was outside the bounds of the array"` in a 500 response, which is a generic .NET error message that could appear on any misconfigured ASP.NET application, not just those with the Telerik vulnerability. The second request helps but the combination may still fire on non-Telerik endpoints returning similar errors.
- **CVE-2020-3161 path specificity** (`http/cves/2020/CVE-2020-3161.yaml`): Sending an oversized URI to `/odata/v1/` assumes the Cisco IP Phone web server exposes this exact endpoint. Different firmware versions may use different paths, potentially causing false negatives.
- **Version detection gap in CVE-2020-8218 and CVE-2020-8260**: Both Pulse Secure templates detect the product's presence but do not verify whether the installed version is actually vulnerable. This could lead to false positives on patched systems that still expose the same endpoints.
- **No negative test cases**: There are no companion test fixtures or expected-output files to validate that these templates do not match against patched versions.

### Suggestions
- **CVE-2017-9248.yaml:44-53**: Consider adding a matcher for the `Telerik.Web.UI` string in the first request as well (not just the second), or combine both requests into a single flow with stricter conditions. This would reduce false positives on generic .NET 500 errors:
  ```yaml
  # Add to first request matcher:
  - 'contains(header, "Telerik") || contains(body, "Telerik.Web.UI")'
  ```
- **CVE-2020-3161.yaml:38**: The `Content-Length` extraction via regex (`[0-9]+`) should validate that the response actually comes from a Cisco IP Phone. Consider adding a `Server` header check (e.g., `contains(header, "Cisco")`) to reduce false positives.
- **CVE-2018-2380.yaml:50-60**: The SAP CRM template path `/sap/crm/` is correct but the traversal payload `../../../` in the detection probe could be flagged by WAFs. Consider documenting this as a known limitation in the template description.
- **All templates**: Consider adding `max-redirects: 0` to prevent the scanner from following redirects into authentication pages, which could cause unexpected matcher behavior.
- **Metadata consistency**: Some templates use `verified: true` while others use `verified: false`. Since these are newly authored templates that have not been tested against live vulnerable instances, setting all to `verified: false` until confirmed would be more accurate.

### Confidence
**Score: High**
These are well-structured nuclei YAML templates following established conventions, the diff is fully readable, and the security domain (CVE detection templates) has clear best practices to evaluate against.

---
*Reviewed by [claude-review](https://github.com/claude-builders-bounty/claude-builders-bounty) v1.0.0*
