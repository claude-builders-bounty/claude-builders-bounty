# Real PR review executions

These are actual executions of the finished CLI using real PR inputs and
attributed, recorded ChatGPT responses. They are **not live Claude runs**.
The headers in both generated Markdown files preserve that distinction.

| Output | Public pull request | Reviewed head | Reviewed base |
| --- | --- | --- | --- |
| [pr-review-1.md](pr-review-1.md) | https://github.com/psf/requests/pull/6731 | `da96a92e2eb6dfe7c74704267bcb8f9fd6fb92b0` | `0e322af87745eff34caffe4df68456ebc20d9068` |
| [pr-review-2.md](pr-review-2.md) | https://github.com/psf/requests/pull/6710 | `92075b330a30b9883f466a43d3f7566ab849f91b` | `970e8cec988421bd43da57350723b05c8ce8dc7e` |

The first PR is a closed, unmerged draft about SSL-context reuse and CA-bundle
loading. The second was merged and promotes a TLS-aware adapter hook. Selection
was based on small, concrete changes with meaningful compatibility and regression
risks, not on fabricated pull requests.

On 2026-09-22, GitHub connector `get_pr_info` and `get_pr_diff` retrieved each PR.
Snapshots retain the full diff, original description and normalized REST metadata.
File counts and additions/deletions are checked before constructing the model
request. The ChatGPT model read the complete inputs and produced the recorded
JSON responses. The CLI verified each response's request hash, validated its
schema, and rendered the committed Markdown. No output file was manually edited
after rendering. No PR code or tests were executed. No review was posted to the
Requests project.

Reproduce from `agents/pr-review` without API keys or network access:

```sh
python scripts/reproduce_examples.py --check
```

To regenerate the two output files, omit `--check`. A single explicit invocation:

```sh
python -m claude_review \
  --pr https://github.com/psf/requests/pull/6731 \
  --snapshot examples/fixtures/requests-6731.snapshot.json \
  --response-file examples/fixtures/requests-6731.response.json \
  --output examples/pr-review-1.md
```

The matching model request can be inspected without calling any model:

```sh
python -m claude_review \
  --pr https://github.com/psf/requests/pull/6731 \
  --snapshot examples/fixtures/requests-6731.snapshot.json \
  --export-request request.json
```

Changing the prompt, schema, metadata or diff changes the request digest and
invalidates its old recorded response. This provides reproducibility, not a
cryptographic signature from a model vendor. Live backend tests still require
Anthropic credentials and network access; see the main README and validation
record. The recorded path is prohibited from publishing comments.
