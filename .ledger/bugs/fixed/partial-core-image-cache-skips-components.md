# Partial grouped image build skipped on resume

## Reproduction

With FORCE_REBUILD=0, interrupt 05-build-images.sh after pipeline-dashboard and
pipeline-agent import but before Markov completes. deploy-all.sh's outer guard
checks only those two core tags and skips the grouped builder, leaving its other
emulator/Markov/Observatory images missing.

## Fix

Always call 05-build-images.sh; its existing per-image checks already honor
FORCE_REBUILD and skip each imported image independently. Default forced rebuild
behavior is unchanged. Shell syntax and whitespace checks pass. The remote resume
reuses completed images and builds the previously missing Markov binary/image.
