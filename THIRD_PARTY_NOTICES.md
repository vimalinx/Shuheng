# Third-Party Notices

Shuheng's own source code is licensed under the MIT License in `LICENSE`.

The Python package declares normal package-manager dependencies. Those
dependencies are installed separately and retain their own licenses; Shuheng
does not vendor their source code into its wheel or source distribution.

Shuheng can interoperate with these separately installed runtimes:

- `@oh-my-pi/pi-coding-agent` — the external OMP executable used by the main
  runtime Provider; distributed by its authors under the MIT License.
- `@earendil-works/pi-coding-agent` — the optional Pi-native worker SDK pinned
  by the sidecar integration; distributed by its authors under the MIT License.

The adapter, sidecar, manifests, and documentation authored in this repository
remain covered by Shuheng's MIT License. External runtime packages and their
transitive dependencies are not redistributed in Shuheng release archives.

Maintainer-local workflow frameworks and their generated state are ignored and
are not part of the Shuheng public source distribution.
