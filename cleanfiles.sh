#!/bin/bash
for i in $(find cpqa scripts | egrep "\.pyc$|\.py~$|\.pyc~$|\.bak$|\.so$") ; do rm -v ${i}; done
rm -v MANIFEST
rm -vr dist
rm -vr build
