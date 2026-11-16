# Extracted source workspace

The outer repository contains the product plan and two tracked upstream source
archives. Those archives contain real application source even though the outer
repository does not yet contain an original application implementation.

## Current organization

Run from the existing checkout:

```sh
cd /workspace/Mullvad-VPN
python3 tools/extract_upstreams.py
```

```text
Mullvad-VPN/
├── docs/                         Product planning and this source guide
├── tools/extract_upstreams.py    Repeatable extraction and source verification
├── mullvadvpn-app-main.zip       Original archive, retained in Git
├── amnezia-client-dev.zip        Original archive, retained in Git
└── build/upstream/               Generated local source trees; Git-ignored
    ├── manifest.json            Archive hashes, metadata and symlink inventory
    ├── mullvad/                 Main source tree; original internal paths
    │   ├── Cargo.toml           Rust workspace
    │   ├── mullvad-daemon/      Background VPN service
    │   ├── talpid-core/         Native networking components
    │   ├── desktop/             TypeScript/React/Electron desktop application
    │   ├── android/             Android application
    │   └── ios/                 iOS application
    └── amnezia/                 Separate upstream source tree
        ├── CMakeLists.txt       C++/Qt build entry point
        ├── client/             Core, QML UI and platform integrations
        ├── service/            Privileged desktop service
        └── recipes/            Native dependency build recipes
```

The helper verifies the bundled archive SHA-256 hashes, preserves executable
permissions and symlinks, and compares every extracted file with the archive.
Repeating it verifies existing sources and refuses to overwrite modified source
files. The hashes detect changes to these bundled archives; they do not establish
upstream authenticity. ZIP comments are recorded as metadata, not trusted Git
commit verification.

The original archives, build manifests, licenses and source files are unchanged.
Internal upstream directories stay together because their build files depend on
relative paths. Generated sources are excluded by the existing `build/` ignore
rule. Commit the helper and guide to preserve recovery instructions; rerun the
command after a fresh checkout. Changes made only inside `build/upstream/` are
local and will not be preserved by a Git commit of the outer repository. Move
future development into a separately planned, tracked component before editing
upstream application code.

Mullvad includes an installation symlink to
`/opt/Mullvad VPN/resources/mullvad-problem-report`; extraction preserves the link
without installing its target. Its Android links are also preserved.

## Language boundaries

| Area | Mullvad | Amnezia |
| --- | --- | --- |
| Native VPN service/core | Rust | C++17 |
| Desktop interface | TypeScript, React, Electron | QML/Qt with C++ |
| Android | Kotlin/Compose with Rust components | Kotlin/Java and native components |
| iOS | Swift and platform components | Swift/Objective-C++ and native components |
| Build system | Cargo, npm, platform SDKs | CMake, Qt, Conan, platform SDKs |

For the planned Chrome browser-proxy prototype, use TypeScript as the primary
application language for the extension, control API and shared schemas, subject
to the existing dependency audit. Keep a maintained proxy as a separate service.
This is consistent with proposed ADR-008 in `DECISIONS.md`; it does not select or
install dependencies.

A future original application could use `apps/extension/`, `services/control-api/`,
`packages/shared/` and `infra/proxy/`. These are proposed paths, not implemented
components. Native clients remain a separate later milestone in the current plan.

For a native VPN product, choose a core implementation and connect interfaces
through defined APIs/IPC. Converting all native networking and mobile code to
TypeScript would require a substantial rewrite and new platform/security tests.
It is practical to standardize application logic; native OS integrations and
established networking implementations can keep their supported languages.

## Build readiness and licensing

Extraction is complete; application build and VPN behavior are not verified.
Both archives omit files from their declared Git submodules:

- Mullvad: `dist-assets/binaries`, `ios/wireguard-apple`.
- Amnezia: `client/3rd/qtkeychain`, `client/3rd/SortFilterProxyModel`,
  `client/3rd/amneziawg-apple`, `client/3rd/qtgamepad`.

The matching revisions and required platform-specific dependencies must be
restored before claiming complete build inputs. ZIPs have no Git metadata for
running `git submodule update` inside the extracted trees.

Mullvad declares Rust 1.100.0, with desktop Volta pins Node 24.21.0 and npm 12.2.0.
Amnezia declares CMake >=3.25, C++17, Qt >=6.10 and Conan. These declarations were
inspected; their toolchains have not been installed or validated here.

Both sources include GPLv3 license texts; Mullvad manifests declare
`GPL-3.0-or-later`. Preserve their notices and review dependency/distribution
obligations before adaptation. Translating source to another language does not
automatically remove its license obligations. No product license was selected.

Validation performed: extraction and full archive-to-source comparison for both
archives, a repeat run verifying existing sources, and a Git ignore check for
both generated trees. No VPN service was started, no runtime tests were run,
and no hosting or paid service was provisioned.
