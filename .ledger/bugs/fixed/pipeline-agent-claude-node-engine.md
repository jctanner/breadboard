# Pipeline-agent installs a CLI outside its declared Node engine range

Fresh image builds install Claude 2.1.322, which declares Node >=22, while the
Debian nodejs package supplies Node 20.19.2. Its version command happens to run,
but that does not make Node 20 a supported runtime for the installed package.

Copy only the official Node 24 executable/npm modules into the Python runtime,
recreate npm/npx links, and check Python/Node/Claude versions during the build.
Set NODE_EXTRA_CA_CERTS to the injected public CA because the official Node binary
uses bundled roots by default. The target build passes all version checks. The
public certificate's non-root readability is tracked and validated separately.
