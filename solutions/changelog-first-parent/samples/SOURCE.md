# Public repository sample

Source: https://github.com/pallets/itsdangerous

Generated on 2026-09-09 from HEAD `672971d66a2ef9f85151e53283113f33d642dabd`.
The first-parent release boundary was tag `2.1.x`, resolving to
`3ddb1ce418712d02f674a171b3f13ab20f6839a7`.
An independent `git rev-list` comparison found all 60 commits in that range
exactly once in `CHANGELOG.md`, with zero missing or duplicate commit IDs.

To reproduce from the solution directory:

```bash
git clone --bare --template= https://github.com/pallets/itsdangerous.git sample-repo.git
git -C sample-repo.git update-ref HEAD 672971d66a2ef9f85151e53283113f33d642dabd
bash changelog.sh --repo sample-repo.git --output sample-CHANGELOG.md
```

Use a fresh disposable clone for reproduction. The command pins only that
clone; it must not be run against an existing development checkout. The sample
contains public commit subjects and IDs, not private repository data. The
tool itself does not fetch, checkout, run project code or change Git refs.

## Source License

Copyright 2011 Pallets

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
