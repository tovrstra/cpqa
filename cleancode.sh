#!/bin/bash
echo Cleaning python code in \'`pwd`\' and subdirectories
for file in README $(find scripts cpqa | egrep "(\.rst$)|(\.py$)|(\.c$)|(\.h$)|(\.i$)|(\.pyf$)"); do
  echo Cleaning ${file}
  sed -i -e $'s/\t/    /' ${file}
  sed -i -e $'s/[ \t]\+$//' ${file}
  sed -i -e :a -e '/^\n*$/{$d;N;ba' -e '}' ${file}
done
