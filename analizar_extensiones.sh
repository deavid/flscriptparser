#!/bin/bash
PRJPATH=$1
BUILDPATH=$2

# Para calcular todas las extensiones:
# for i in ext*-*; do eneboo-assembler build $i fullpatch; eneboo-assembler build $i revfullpatch; done

# for i in ext*-*; do test -f "$i/build/fullpatch/fullpatch.xml" || { echo $i; eneboo-assembler build $i fullpatch; } done
# for i in ext*-*; do test -f "$i/build/revfullpatch/revfullpatch.xml" || { echo $i; eneboo-assembler build $i revfullpatch; } done

if [ -z "$BUILDPATH" ]; then
    rm .patchtest/$PRJPATH.ext.*
    echo /home/gestiweb/git/eneboo-features-fede/*/build | xargs -d ' ' -n1 -P2 $0 $1
    exit 0;
fi
UNPATCHPATH=$BUILDPATH/revfullpatch
REPATCHPATH=$BUILDPATH/fullpatch
MAINPATCH=$BUILDPATH/../patches/

PATCHNAME=$(echo $BUILDPATH | cut -f6 -d'/')
#echo ":: $PRJPATH -- $PATCHNAME "


test -f "$UNPATCHPATH/revfullpatch.xml" || { echo "NO EXISTE :: $UNPATCHPATH/revfullpatch.xml"; exit 1; }
test -f "$REPATCHPATH/fullpatch.xml" || { echo "NO EXISTE :: $REPATCHPATH/fullpatch.xml"; exit 2; }
test -d "$MAINPATCH" || { echo "NO EXISTE :: $MAINPATCH"; exit 3; }

mkdir -p ".patchtest/$PRJPATH/"

DSTFOLDER=.patchtest/$PRJPATH/$PATCHNAME-uninstall
test -d "$DSTFOLDER" || \
eneboo-mergetool folder-patch "$UNPATCHPATH" "$PRJPATH" "$DSTFOLDER" >/dev/null 2>&1


DSTFOLDER2=.patchtest/$PRJPATH/$PATCHNAME-reinstall
test -d "$DSTFOLDER2" || \
eneboo-mergetool folder-patch "$REPATCHPATH" "$DSTFOLDER" "$DSTFOLDER2" >/dev/null 2>&1


diff -rN -t -b -d -U1 --exclude=".git"  -x '*.png' -x '*.jpg' -x "*.qry" \
    -x "*.kut" -x "*.ui" -x '*~' -x '*.*.*' "$PRJPATH" "$DSTFOLDER" > "$DSTFOLDER.patch"

    diff -rN -t -b -d -U1 --exclude=".git"  -x '*.png' -x '*.jpg' -x "*.qry" \
    -x "*.kut" -x "*.ui" -x '*~' -x '*.*.*' "$DSTFOLDER" "$DSTFOLDER2" > "$DSTFOLDER2.patch"

grep -aE "^-[^-]" "$DSTFOLDER.patch" > "$DSTFOLDER.patch.grep"
grep -aE '^\+[^\+]' "$DSTFOLDER2.patch" > "$DSTFOLDER2.patch.grep"

#rm "$DSTFOLDER" -R
#rm "$DSTFOLDER2" -R

BYTES_UNPATCH=$(cat "$DSTFOLDER.patch.grep" | wc -c)
BYTES_REPATCH=$(cat "$DSTFOLDER2.patch.grep" | wc -c )

BYTES_MAINPATCH=$(du -bs $MAINPATCH --exclude='*.png' --exclude='*.jpg' --exclude="*.qry" \
    --exclude="*.kut" --exclude="*.ui" --exclude="*~" | cut -f1)

BYTES_MIN=$(( $BYTES_MAINPATCH / 2))
BYTES_MIN2=$(( $BYTES_MAINPATCH / 5))

DEST=.patchtest/$PRJPATH.ext.others.txt
if [ "$BYTES_UNPATCH" -lt "$BYTES_MIN2" ]; then
    exit 0;
fi

if [ "$BYTES_UNPATCH" -gt "$BYTES_MIN" -a "$BYTES_REPATCH" -gt "$BYTES_MIN" ]; then
    DEST=.patchtest/$PRJPATH.ext.installed.txt
    echo "EXTENSION   :: $PATCHNAME - patch: $BYTES_MAINPATCH reinstall: $BYTES_REPATCH uninstall: $BYTES_UNPATCH"
    echo $PATCHNAME >> $DEST
    exit 0;
fi

if [ "$BYTES_UNPATCH" -gt "$BYTES_MIN" ]; then
    DEST=.patchtest/$PRJPATH.ext.unsure.txt
    echo "UNSURE      :: $PATCHNAME - patch: $BYTES_MAINPATCH reinstall: $BYTES_REPATCH uninstall: $BYTES_UNPATCH"
    echo $PATCHNAME >> $DEST
    exit 0;
fi

if [ "$BYTES_UNPATCH" -gt "$BYTES_MIN2" -a "$BYTES_REPATCH" -gt "$BYTES_MIN2" ]; then
    DEST=.patchtest/$PRJPATH.ext.unsure.txt
    echo "UNSURE      :: $PATCHNAME - patch: $BYTES_MAINPATCH reinstall: $BYTES_REPATCH uninstall: $BYTES_UNPATCH"
else
    echo "            :: $PATCHNAME - patch: $BYTES_MAINPATCH reinstall: $BYTES_REPATCH uninstall: $BYTES_UNPATCH"
fi


echo $PATCHNAME >> $DEST
