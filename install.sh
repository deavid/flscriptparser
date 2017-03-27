#!/bin/bash
[[ $(basename $(pwd)) != "flscriptparser" ]] && {
    echo "This program MUST be run from its folder!!!"
    exit 1
}
DEPS=$(cat dependencies.debian)
aptitude install $DEPS -y
while read line; do
    test -e /usr/local/bin/fldesigner && unlink /usr/local/bin/fldesigner 
    ln -s "$line" /usr/local/bin/fldesigner
    break
done < <(find /usr/local/ -type f -name designer)

while read line; do
    bname=$(basename "$line")
    test -h /usr/local/bin/$bname && unlink /usr/local/bin/$bname
    ln -s "$line" /usr/local/bin/$bname
done < <(find $(pwd) -executable -type f \! -path "*/.*")
test -f /usr/local/bin/flscriptparser && unlink /usr/local/bin/flscriptparser

exit 0

