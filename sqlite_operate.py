# encoding: utf-8

"""
@author: lin
@license: (C) Copyright 2013-2017, Node Supply Chain Manager Corporation Limited.
@contact: 739217783@qq.com
@software: Pycharm
@file: sqlite_operate.py
@time: 2022/12/17 15:26
@desc:
"""
import sqlite3
import os

class DBOperate:

    def __init__(self,dbPath=os.path.join(os.getcwd(),"db")):
        self.dbPath=dbPath
        self.connect=sqlite3.connect(self.dbPath)

    def Query(self,sql:str)->list:
        """"""
        queryResult = self.connect.cursor().execute(sql).fetchall()
        return queryResult

    def QueryAsDict(self,sql:str)->dict:
        """调用该函数返回结果为字典形式"""
        self.connect.row_factory=self.dictFactory
        cur=self.connect.cursor()
        queryResult=cur.execute(sql).fetchall()
        return queryResult

    def Insert(self,sql:str):
        # print(f"执行的sql语句为\n{sql}")
        self.connect.cursor().execute(sql)
        self.connect.commit()

    def Update(self,sql:str):
        self.connect.cursor().execute(sql)
        self.connect.commit()


    def Delete(self,sql:str):
        self.connect.cursor().execute(sql)
        self.connect.commit()

    def CloseDB(self):
        self.connect.cursor().close()
        self.connect.close()

    def dictFactory(self,cursor,row):
        """将sql查询结果整理成字典形式"""
        d={}
        for index,col in enumerate(cursor.description):
            d[col[0]]=row[index]
        return d

    def dictResult(self,sql):
        """
        用于读取已爬过链接
        @param sql:
        @return:
        """
        data = {}
        sqlite_data = self.connect.cursor().execute(sql)
        for title, url in sqlite_data:
            data[title] = url

        return data

if __name__ == '__main__':
    db=DBOperate('a.db')
    # insertSql="""REPLACE INTO sample_list (ID,case_name,total_number,selected_number,ADic,MDic_R,
    #             MDic_C,MFCA,FCCA,check_status,check_person,check_time,review_status,review_person,
    #             review_time,report_status,report_person,report_time)
    #             VALUES( 'Test-1','unknown',132,12,1,2,3,4,5,'已检查','admin','2020-04-22 17:22:23',
    #             '通过','admina','2020-04-22 17:22:25','已生成','admina','2020-04-22 17:26:23')"""
    sql=f"""SELECT * FROM COMPANY"""
    print(db.QueryAsDict(sql))
    # print(db.Query("SELECT * FROM sample_list"))
