import argparse
import os
import time
import subprocess


parser = argparse.ArgumentParser(description='Process svn cleanup and svn update')

parser.add_argument('dir', metavar='DIR', type=str, help='input the local address of the SVN repo')

args = parser.parse_args()

repo_dir = args.dir.split('=')[-1]

#repo_dir = "/mnt/data0/proj_osgeo/data_svn/svn_repos/mapguide"
e = BaseException
while e!= None :
    e = None
    os.chdir(repo_dir)
    my_args = []
    my_arg1 = "svn cleanup"
    my_arg2 = "svn update --ignore-externals"
    my_args.append(my_arg1)
    my_args.append(my_arg2)
    
    try:
        retcode = subprocess.run( my_arg1, cwd= repo_dir, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        print("SVN cleaned up!", retcode.stdout)
        retcode = subprocess.run( my_arg2, cwd= repo_dir, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        if retcode.returncode == 28:
            print("tmp FULL!", retcode.returncode)
            #print(retcode)
            raise IOError(retcode.stderr)
        elif retcode.returncode == 120106:
            print("HTTP terminated by server! wait 3min and restart!", retcode.returncode)
            time.sleep(180)
            raise ConnectionRefusedError(retcode.stderr)
        elif retcode.returncode!=0 :
            print("Error!", retcode.returncode)
            raise BaseException(retcode.stderr)
    except BaseException as err:
        print("Execution failed:", err)
        print(retcode.stdout)
        e = err
        continue