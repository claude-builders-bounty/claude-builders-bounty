### Summary

This PR adds 10 new nuclei vulnerability detection templates for CISA Known Exploited Vulnerabilities (KEV), targeting Pulse Secure/Ivanti VPN appliances, Cisco IP Phones, SAP CRM, Telerik UI, Array Networks, Apache Struts, and Cisco IOS XE. All templates use detection-only matchers without exploitation payloads.

### Risk Assessment

- **False positive risk in CVE-2017-9248**: The matcher checks for a generic .NET error message that could appear on any misconfigured ASP.NET application
- **Version detection gap in CVE-2020-8218 and CVE-2020-8260**: Both Pulse Secure templates detect the product but do not verify whether the installed version is actually vulnerable
- **Missing `max-redirects`**: Several templates follow redirect chains which could lead to matcher issues on misconfigured servers

### Suggestions

1. Consider adding a `Server` header check to reduce false positives on CVE-2017-9248
2. Add `max-redirects: 0` to templates that should not follow redirects
3. Add version extraction logic to CVE-2020-8218 and CVE-2020-8260 for more precise detection

### Confidence

**Score: High** 鈥?Well-structured YAML templates following established conventions with clear best practices to evaluate against.
