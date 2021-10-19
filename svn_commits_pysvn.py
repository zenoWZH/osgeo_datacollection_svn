#coding=utf-8
import re
import pysvn
import datetime
import time
import pandas as pd


from sqlalchemy import create_engine
from sqlalchemy import types as sqltype
from config.database import HOST, PORT, USER, PASSWORD, DATABASE

import psycopg2

import gc

def escape(s):
    return (s).replace('\'','\'\'').replace("\\","\\\\")

#寻找svn账户的邮箱
def save_aliase(entry, urladd):
    try:
        db = psycopg2.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            database=DATABASE)
            #charset='utf8')
        cursor = db.cursor()
    except Exception as e:
        print("Database connect error:%s" % e)
    
    try:
        svn_id = entry.author
    except BaseException as err:
        #print("Adding Aliase Error:",err)
        svn_id = "noauthor"
    if '@' in svn_id:
        svn_mail = svn_id
    else:
        svn_mail = svn_id+'@'+urladd
    source = "SVN"
    

    sql_aliase = """INSERT INTO aliase(aliase_id, mailaddress, source)
                                    values('%s', '%s', '%s')""" % (
    svn_id, svn_mail, source)

    try:
        db.commit()
        cursor.execute(sql_aliase)
        db.commit()
    except Exception as err:
        sql_aliase = """UPDATE aliase SET mailaddress ='%s', source='%s' WHERE aliase_id='%s'"""% (
                        svn_mail, source, svn_id)
            
        db.commit()
        cursor.execute(sql_aliase)
        db.commit()
        #print(err)

    return svn_id

def save_one_filelog(entry, proj, filelog):
    try:
        db = psycopg2.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            database=DATABASE)
            #charset='utf8')
        cursor = db.cursor()
    except Exception as e:
        print("Database connect error:%s" % e)
    try:
        svn_commiter_id = entry.author
    except BaseException as err:
        #print("Aliase Error:",err)
        svn_commiter_id = "noauthor"

    rev_number = str(entry.revision.number)

    id_commit = proj+'#'+rev_number+'#'+svn_commiter_id
    id_filelog = id_commit+'#'+filelog.path
    source = "SVN"

    if filelog.copyfrom_path!= None :
        fadded = filelog.copyfrom_revision.number
        fremoved = filelog.copyfrom_path
    else:
        fadded = "None"
        fremoved = "None"

    sql = """INSERT INTO filelog(filelog_id, commit_id, action, file_name, added, removed)
            values('%s', '%s', '%s','%s', '%s', '%s')""" % (escape(id_filelog), id_commit, filelog.action, escape(filelog.path), fadded, escape(fremoved))

    try:
        db.commit()
        cursor.execute(sql)
        db.commit()
        #print("%s : Insert successfully" % entry['id'])
    except Exception as e:
        try:  # 插入失败表示数据库存在此entry，转为update更新
            db.commit()
            #print("Exception: %s" % e)
            sql_update = """UPDATE filelog SET
              commit_id='%s', action='%s', file_name='%s', added='%s', removed='%s'
             WHERE filelog_id='%s'""" % (id_commit, filelog.action, escape(filelog.path), fadded, escape(fremoved), escape(id_filelog))
            cursor.execute(sql_update)
            db.commit()
            #print("%s : Update successfully" % entry['id'])
        except Exception as err:
            print("Save filelog Exception: %s" % err)
            print("update error:%s" % err)
            db.rollback()

def save_one_svncommit(entry, proj):
    try:
        db = psycopg2.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
            database=DATABASE)
            #charset='utf8')
        cursor = db.cursor()
    except Exception as e:
        print("Database connect error:%s" % e)
    try:
        svn_commiter_id = entry.author
    except BaseException as err:
        #print("Aliase Error:",err)
        svn_commiter_id = "noauthor"
    
    rev_number = str(entry.revision.number)
    id_commit = proj+'#'+rev_number+'#'+svn_commiter_id
    source = "SVN"
    
    time_format = "%Y-%m-%d %H:%M:%S"
    struct_time = datetime.datetime.fromtimestamp(entry.date)
    t_commit = datetime.datetime.strftime(struct_time, time_format)
    

    sql = """INSERT INTO commit(commit_id, proj_id, commiter_aliase_id, commit_message, commit_timestamp, commit_sha, commit_parents, commit_refs)
                                        values('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')""" % (
        id_commit, proj, svn_commiter_id, escape(entry.message), t_commit, rev_number, entry.revision.kind, source)

    try:
        db.commit()
        cursor.execute(sql)
        db.commit()
        #print("%s : Insert successfully" % entry['id'])
    except Exception as e:
        try:  # 插入失败表示数据库存在此entry，转为update更新
            db.commit()
            #print("Exception: %s" % e)
            sql_update = """UPDATE commit SET
             proj_id='%s', commiter_aliase_id='%s', commit_message='%s', commit_timestamp='%s', commit_sha='%s', commit_parents='%s', commit_refs='%s'
             WHERE commit_id='%s'""" % (proj, entry.author, escape(entry.message), t_commit, rev_number, entry.revision.kind, source, id_commit)
            cursor.execute(sql_update)
            db.commit()
            #print("%s : Update successfully" % entry['id'])
        except Exception as err:
            print("Save commit Exception: %s" % err)
            print("update error:%s" % err)
            db.rollback()


###########################################################
df = pd.read_csv("../svn_repository.csv")
svn_source_url = df["Repos"].values
###########################################################

#coding=utf-8

for work_dir in svn_source_url:
    #work_dir = '/mnt/data0/proj_osgeo/data_svn/svn_repos/gvsig-desktop/gvsig-desktop'
    #proj = gvsig-desktop
    proj = str(df.loc[df["Repos"] == work_dir]["Projects"].values[0]).lower()
    urladd = work_dir.split("//")[1].split('/')[0]
    print(proj, urladd)
    client = pysvn.Client()

    try:
        local_dir = str(df.loc[df["Repos"] == work_dir]["Local"].values[0])
        entry = client.info(local_dir)
        print ('SVN路径:',entry.url)
        print ('最新版本:',entry.commit_revision.number)
        print ('提交人员:',entry.commit_author)
        print ('更新日期:', datetime.datetime.fromtimestamp(entry.commit_time))

    except BaseException as err:
        print("No local!")
        local_dir = work_dir
        print("Pull from remote:" + work_dir)
        

    


    #列出最近更新5版本的文件列表
    entries_list = client.log(local_dir, discover_changed_paths=True)
    print("Successfully Pulled all logs.")
    for entry in entries_list:
        try:
            #print(re.findall(r"\d+",str(entry.revision)),entry.message)
            save_aliase(entry, urladd)
            save_one_svncommit(entry, proj)
            for filelog in entry.changed_paths:
                save_one_filelog(entry, proj, filelog)
        except BaseException as err:
            print(err)
        finally:
            gc.collect()
            
