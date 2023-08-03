# Git cheatsheet

## Set username & email
```shell
git config user.name igrek51
git config user.email me@gmail.com
```

## Disable SSL verify
```shell
git config http.sslVerify false
```

## Enable credentials store
```shell
git config --global credential.helper store
```

## Amend commit author
```shell
git commit --amend --author="Me <me@example.com>"
```

## Amend commit date
```shell
export GIT_COMMITTER_DATE="Wed Mar 3 17:46:54 2021 +0100"
git commit --amend --date "$GIT_COMMITTER_DATE"
```

## Rebase
Reapply commits from `HEAD` to `FORK_POINT` on top of the `master`:
```shell
git rebase -i --onto origin/master --fork-point <FORK_POINT>
```
`FORK_POINT` - (branch or commit) last common ancestry which is cut down

## Squash branch
```shell
git reset --soft `git merge-base HEAD origin/master`
git commit
```

## Find commits only on that branch
```shell
git lg origin/master..HEAD
```

## Check if there would be merge conflicts
```shell
git merge --no-commit origin/master
# check the return code here
git merge --abort
```

## Cherry pick with 'no commit'
```shell
git cherry-pick -n COMMIT_HASH
```

## Track remote branch
```shell
git branch -u origin/branch
```

## Add brach alias
```shell
git symbolic-ref refs/heads/om refs/remotes/origin/master
```

## Cancel commit / merge when typing message in vim
`:cq`

## Revert changes from commit from file
```shell
git show some_commit_sha1 -- some_file | git apply -R
```

## Delete tag
```shell
TAG=1.0.0
git tag --delete $TAG
git push --delete origin $TAG
```

## Equalize 2 branches
```shell
BRANCH_FROM=feature
BRANCH_TO=master
git checkout $BRANCH_FROM
git diff --full-index --binary $BRANCH_FROM $BRANCH_TO | git apply --index
git commit -m "Resolve diffs from $BRANCH_FROM to $BRANCH_TO"
```

## Patch and apply
```shell
git format-patch -1 HASH
git am PATCH.patch
```

## Differences between local and remote
```shell
git diff --full-index --binary origin/$(git rev-parse --abbrev-ref HEAD) HEAD
```
