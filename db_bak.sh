#!/bin/bash
filename=auto_test_$(date "+%Y%m%d%H%M%S").sql

# 备份sql
mysqldump -uroot -pbzl123456 auto_test>/root/db_bak/data/${filename}

echo "$(date '+%Y:%m:%d %H:%M:%S')----------add db file $filename----------">>/root/db_bak/log.txt
# 删除15天前的备份sql

file_list=`find /root/db_bak/data -mtime +15 -type f -name "*.sql"`
for file in ${file_list[@]};do
        rm -rf $file
        echo "$(date '+%Y:%m:%d %H:%M:%S')----------del db file $file----------">>/root/db_bak/log.txt
done