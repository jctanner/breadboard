## What do you want to work on?
## Describe the change you want to make. Link to an existing issue if there is one.

I've been working on an integration of fullsend and https://github.com/jctanner/breadboard. Breadboard is a k3s stack with emulators for jira, github, gitlab, runners, and openshell. Incorporating fullsend within breadboard creates an all-encompassing devstack: github apps, token minting, openshell runners, secret management, webhooks/events, etc, etc etc. Developers could experience and develop and test the entire stack in full local isolation, without munging anything on github.com.

To make that integration seamless and compliant, I would like to implement a few initial changes:

- hardcoded assumptions about the forge domain being github.com
- passing GH_HOST & GH_ENTERPRISE_TOKEN to the runner and into the sandbox so we can use hosts other than github.com with the "gh" cli.
- allow a configurable runner label so in an environment outside github.com, we're not stuck with "ubuntu-24.04"

These changes would not be untested AI-slop. The integration is already fully functional and well tested. The patches I'll propose are verified in a live environment.


## Why this change?
## Explain your motivation and why this matters. Keep it concise.

Every stack I've ever worked on that can't be run completely locally, has been a bad experience. In most cases you end up with a "commit, push & pray" model. If fullsend is to become the central platform we're all using for agentic sdlcs, having a local solution is going to be paramount for developer adoption, broader innovation and reduction of wasted CI credits & developer time.
