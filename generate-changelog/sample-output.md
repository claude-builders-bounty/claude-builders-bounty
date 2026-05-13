# Sample Output

Tested against the real GitHub repository `fastify/fastify` on May 12, 2026.

Command:

```bash
git clone --depth 120 https://github.com/fastify/fastify.git /tmp/changelog-test-fastify
cp changelog.sh /tmp/changelog-test-fastify/changelog.sh
cd /tmp/changelog-test-fastify
bash changelog.sh --output CHANGELOG.generated.md
```

Result:

```markdown
# Changelog

Generated on 2026-05-12 using commits since v5.8.5.

## Unreleased

### Added
- add bestforandroid (#6659) ([dc48d11e](https://github.com/fastify/fastify/commit/dc48d11ecbbbd0d341cc475da65b1193b4908e60), 2026-04-15, Manuel Spigolon)
- add request.mediaType (#6653) ([890ab757](https://github.com/fastify/fastify/commit/890ab7578f14730b2fed6de43acfeee19da1a3e4), 2026-04-15, KaKa)
- add support of onMaxParamLength (#6716) ([1c499748](https://github.com/fastify/fastify/commit/1c49974805e57a17f1616f422678317b1d35b73f), 2026-05-08, KaKa)
- add typeof guard before toString.call in send and onSendEnd (#6693) ([aab339f7](https://github.com/fastify/fastify/commit/aab339f7b0c75da93e48bce77578c77c5e3ccd27), 2026-04-30, aqu)

### Fixed
- avoid duplicate closeIdleConnections call on native servers (#6669) ([c2ba18c1](https://github.com/fastify/fastify/commit/c2ba18c17769dacce61472ec0397560b3b4eebde), 2026-04-19, Trivikram Kamat)
- correct isCustomSerializerCompiler flag check (#6657) ([d76dbcd5](https://github.com/fastify/fastify/commit/d76dbcd58bf6d82bba167cdc74a79d2f74dbcb97), 2026-04-21, Ran)
- enable diagnostics tracking for async error handlers (#6458) ([6d202c62](https://github.com/fastify/fastify/commit/6d202c6203f33ceb709dbcf6311b2d7152a8a057), 2026-05-07, Alireza Mohagheghi)
- error.code not present on some routing errors (#6674) (#6678) ([d9659819](https://github.com/fastify/fastify/commit/d9659819fbbc391d054f1aa4b49ce969a13610dd), 2026-04-19, Matteo Collina)
- guard forwarded host and protocol on socket presence (#6684) ([21b4c3c1](https://github.com/fastify/fastify/commit/21b4c3c101038030e552ad2cfcca3f43a349f464), 2026-04-24, Matteo Collina)
- ignore duplicate trailer completions (#6714) ([9026164f](https://github.com/fastify/fastify/commit/9026164f5a2e78db59ff8f98933279161a85a6e3), 2026-05-07, Matteo Collina)
- prevent duplicate res.end in sendTrailer with sync callbacks (#6676) ([d33f017f](https://github.com/fastify/fastify/commit/d33f017ffef3a9beec687b4d4b1777e2e1180afa), 2026-04-19, KaKa)
- use ContentType parser for response schema lookup (#6685) ([c06fc06d](https://github.com/fastify/fastify/commit/c06fc06d33e66354cf6f5dc000b1ef2002a5eb96), 2026-04-21, Ulises Gascon)
- validate invalid route logLevel at registration (#6523) ([2ae3e1d7](https://github.com/fastify/fastify/commit/2ae3e1d73491c023080efed566204c470cb49fd0), 2026-04-21, Max Petrusenko)

### Changed
- Bump JustinBeckwith/linkinator-action from 2.4.0 to 2.4.2 (#6706) ([291b1f89](https://github.com/fastify/fastify/commit/291b1f89b4250f22d9edbe62a1cf1bfbd5f3f3d1), 2026-05-01, dependabot[bot])
- Bump actions/github-script from 8 to 9 (#6705) ([7cbea084](https://github.com/fastify/fastify/commit/7cbea084a459b74c6ca27f1df704fa7130db16a1), 2026-05-01, dependabot[bot])
- Bump pnpm/action-setup from 5.0.0 to 6.0.4 (#6704) ([e5db7afd](https://github.com/fastify/fastify/commit/e5db7afd9e61e2b15bbbf4299358a4cc407e823e), 2026-05-01, dependabot[bot])
- allow request.getValidationFunction() to return undefined (#6665) ([9bbf6097](https://github.com/fastify/fastify/commit/9bbf60978d013c26663b7be8031ecc12e6db12bd), 2026-04-23, Trivikram Kamat)
- cache parsed ContentType objects in ContentTypeParser (#6694) ([4965dace](https://github.com/fastify/fastify/commit/4965daceab71462e38156acdcf8ef535ddf35df0), 2026-04-28, aqu)
- correct return503OnClosing comment in route.js (#6712) ([10c69d15](https://github.com/fastify/fastify/commit/10c69d153c6ee4a61878eabfb2a8f3ec34ab9c8c), 2026-05-05, Matteo Collina)
- defer ContentType parsing in getSchemaSerializer until needed (#6692) ([6c690505](https://github.com/fastify/fastify/commit/6c69050523defc982e231e616a66be8b291ee73f), 2026-04-26, aqu)
- update contribution rules (#6670) ([d1133d7e](https://github.com/fastify/fastify/commit/d1133d7eac09e075ccfd3b947f6a6e25d727d4d4), 2026-04-21, Antonio Tripodi)
- use shared quality workflow (#6688) ([efb599a7](https://github.com/fastify/fastify/commit/efb599a7ac2b4e5ec148cf6a2f547b6dd3ea4eb7), 2026-04-23, Frazer Smith)

### Removed
- drop Node.js 20 from yarn matrix (#6662) ([dce0d47a](https://github.com/fastify/fastify/commit/dce0d47a44ecf6605a4e6b39d80f0bef17c2c2ce), 2026-04-15, Antonio Tripodi)
- remove deprecated leveldb plugin and update ecosystem (#6661) ([282ff731](https://github.com/fastify/fastify/commit/282ff731c233f2e84ea46c7c73d773ea2a7aea43), 2026-04-15, Antonio Tripodi)
```
