# -*- coding: utf-8 -*-
import os
import zipfile
import time
import fnmatch
import threading


def getReleaseDir():
    ret = os.getcwd() + "/release"  # 工程根目录release下
    try:
        os.makedirs(ret)
    except:
        pass
    return ret


def famatch(fn, matches):
    for m in matches:
        if fnmatch.fnmatch(fn, m):
            return True
    return False


def zipDir(source_dir, target_file, match=['*'], exclude_dirs=[], exclude_files=[], other_py_file=[]):
    myZipFile = zipfile.ZipFile(target_file, 'w')
    for root, dirs, files in os.walk(source_dir):
        for xdir in exclude_dirs:
            if xdir in dirs:
                dirs.remove(xdir)
        if files:
            other_files = list(filter(lambda f: famatch(f, other_py_file), files))
            src_files = list(filter(lambda f: famatch(f, match), files))
            files = list(filter(lambda f: not famatch(f, exclude_files), src_files))
            files = files + other_files
            for vfileName in files:
                fileName = os.path.join(root, vfileName)
                myZipFile.write(fileName, fileName, zipfile.ZIP_DEFLATED)
    myZipFile.close()


# zipDir(source_dir, target_file, match=['*'], exclude_dirs=[], exclude_files=[],other_py_file=[]):
def export_auto():
    import compileall
    old = os.getcwd()
    print('--------    start compile path:--------', old)
    compileall.compile_dir(old)
    # zipDir(source_dir, target_file, match=['*'], exclude_dirs=[], exclude_files=[],other_py_file=[]):
    print('--------    compile finish  --------')
    # os.chdir("../")  # 到上级目录
    print('-------- current path: ', os.getcwd())
    print('-------- release path: ', getReleaseDir())
    print('-------- start zip all files --------')
    zipDir(old,
           getReleaseDir() + '/auto_test.zip',
           ['*'],
           ['images', 'static', 'templates', '.idea', '.svn', 'logs'],  # 忽略编译的文件夹
           ['.*', 'icdat.db', '*.swp', '*.py', '*.orig', '*.zip', 'options.txt', '*.txt', '*.sql',
            'l.txt', '*.7z', '*.doc', 'tftpgui.cfg' , '*.po', '*.log'],
           ['library.zip', 'config.py', '__init__.py', '',  '*zh*.po',
            '*en*.po'])  #'*.sql','*.log', '*.txt','runpool.pyc', 'datacommcenter.pyc', '__init__.pyc'
    print('-------- zip finish --------')
    try:
        os.removedirs(getReleaseDir() + "/doormaster")
    except:
        pass
    # 解压出来的文件有时不完整，手动解压


if __name__ == "__main__":
    print('start package pyc files')
    print('current path:' + os.getcwd())
    print('!!!!!!!!!!!!!!!!    start delete all pyc files !!!!!!!!!!!!!!!!!!!!!!!')
    os.system("del *.pyc /s")
    print('--------   export AUTO TEST   --------')
    export_auto()
    print('/n cab complete!Enjoy!!!:-)')
