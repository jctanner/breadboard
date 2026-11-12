# Privileged mirrors followed source symlinks

Review of the mirror callers found that is_file/copyfile/stat followed a tracked
symlink into host files while the seed ran under sudo. Reject direct and ancestor
symlinks and path escapes both during collection and immediately before copying.
Tests exercise regular files, file/directory symlinks and escaping paths in both
mirrors. Source working trees remain within the documented trusted operator/sudo
boundary; racing that operator is not a supported hostile-user security boundary.

Route source ls-files and mirror git apply through the isolated Git helper. Clear
inherited Git controls instead of maintaining a partial denylist, retaining only
the stricter ownership test hook. Preserve the explicitly selected public CA.
Disable external diff for the fixture diff command.

Also clear the whole fetched mirror working tree before copying, preserving only
.git and unlinking links rather than traversing them. A malicious fetched parent
link must not redirect selective cleanup outside the temporary mirror, and broken
links must not remain as copy destinations. A filesystem regression proves outside
files survive and broken/parent links and stale normal content are removed.
