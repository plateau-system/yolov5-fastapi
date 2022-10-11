#このファイルではAPI用サーバーと検出の処理を非同期で行います。
from time import sleep
import cv2
import os
import datetime
import shutil
import pafy
import subprocess
from subprocess import PIPE
from fastapi import FastAPI
import asyncio
import mysql.connector

# FastAPI(API)、count(初期動作のトリガー)、response_lis(初期値)
app = FastAPI()
count=0
response_lis = [{
    'name' : "None",
    'person' : 0,
    'bicycle' : 0,
    'car' : 0,
    'motorcycle' : 0
}]

def save_frame_camera_cycle():
    global response_lis, count
    count = count+1
    dir_path = 'yolov5-plateau-system/data/images'
    basename = 'camera_capture_cycle'
    ext = 'jpg'

    while True:
        # コネクション作成
        conn = mysql.connector.connect(
            host='host.docker.internal',
            port='3306',
            user='user',
            password='password',
            database='web_system'
        )
        # 接続状況確認
        print(conn.is_connected())
        cur = conn.cursor(buffered=True)
        cur.execute("SELECT id, spots_name, spots_url, spots_day, spots_week, spots_month FROM spots WHERE spots_status=0")
        db_lis = cur.fetchall()
        # DB接続終了
        cur.close()

        detect_lis = []
        if os.path.isdir('yolov5-plateau-system/runs/detect/'):
            shutil.rmtree('yolov5-plateau-system/runs/detect/')

        for i in range(len(db_lis)):
            video = pafy.new(db_lis[i][2])
            best = video.getbest(preftype="mp4")
            cap = cv2.VideoCapture(best.url)
            
            if not cap.isOpened():
                return
            os.makedirs(dir_path, exist_ok=True)
            base_path = os.path.join(dir_path, basename)

            ret, frame = cap.read()
            cv2.imwrite('{}_{}.{}'.format(base_path, datetime.datetime.now().strftime('%Y%m%d%H%M%S%f'), ext), frame)
            
            proc = subprocess.run(['python', 'yolov5-plateau-system/main.py','--save-txt'], stdout=PIPE, stderr=PIPE)
            proc_str = proc.stdout.decode('utf-8').split()
            proc_int = [int(s) for s in proc_str]
            print(proc_str)
            # 返ってきた結果が空だった時の処理
            if not proc_int:
                proc_int = [0, 0, 0, 0]
            # 検出が終わった画像の削除
            target_dir = 'yolov5-plateau-system/data/images/'
            shutil.rmtree(target_dir)
            os.mkdir(target_dir)
            detect_lis.append(proc_int)

        response_lis.clear()
        for i2 in range(len(detect_lis)):
            data = {
                'name' : db_lis[i2][1],
                'person' : detect_lis[i2][0],
                'bicycle' : detect_lis[i2][1],
                'car' : detect_lis[i2][2],
                'motorcycle' : detect_lis[i2][3]
            }
            response_lis.append(data)

        # day 1～24時間、最後にリセット
        # week 過去７日間
        # month 過去３０日間
        for i3 in range(len(db_lis)):
            # day
            if db_lis[i3][3] == 'None':
                count_day = '%s,%s,%s,%s,' % (detect_lis[i3][0], detect_lis[i3][1], detect_lis[i3][2], detect_lis[i3][3])
                cur = conn.cursor(buffered=True)
                sql = ("UPDATE spots SET spots_day = %s WHERE id = %s")
                param = (count_day, db_lis[i3][0])
                cur.execute(sql, param)
                conn.commit()
                cur.close()
            else:
                all_day = db_lis[i3][3].split(',')
                all_day.remove('')
                if len(all_day) >= 96:
                    count_day = '%s,%s,%s,%s,' % (detect_lis[i3][0], detect_lis[i3][1], detect_lis[i3][2], detect_lis[i3][3])
                    cur = conn.cursor(buffered=True)
                    sql = ("UPDATE spots SET spots_day = %s WHERE id = %s")
                    param = (count_day, db_lis[i3][0])
                    cur.execute(sql, param)
                    conn.commit()
                    cur.close()         

                    # week
                    all_day_int = [int(i4) for i4 in all_day]
                    all_day_re = convert_1d_to_2d(all_day_int, 4)
                    ave_day_person = sum([i5[0] for i5 in all_day_re]) / 24
                    ave_day_bicycle = sum([i6[1] for i6 in all_day_re]) / 24
                    ave_day_car = sum([i7[2] for i7 in all_day_re]) / 24
                    ave_day_motorcycle = sum([i8[3] for i8 in all_day_re]) / 24

                    # 初回のみ初期値として0を６日間分入れる+今日の結果
                    if db_lis[i3][4] == 'None':
                        none_week = '0,0,0,0,' * 6
                        count_week = '%s%s,%s,%s,%s,' % (none_week, ave_day_person, ave_day_bicycle, ave_day_car, ave_day_motorcycle)
                        cur = conn.cursor(buffered=True)
                        sql = ("UPDATE spots SET spots_week = %s WHERE id = %s")
                        param = (count_week, db_lis[i3][0])
                        cur.execute(sql, param)
                        conn.commit()
                        cur.close()
                    else:
                        all_week = db_lis[i3][4].split(',')
                        del all_week[0:5]
                        count_week = '%s%s,%s,%s,%s,' % (all_week,ave_day_person, ave_day_bicycle, ave_day_car, ave_day_motorcycle)
                        cur = conn.cursor(buffered=True)
                        sql = ("UPDATE spots SET spots_week = %s WHERE id = %s")
                        param = (count_week, db_lis[i3][0])
                        cur.execute(sql, param)
                        conn.commit()
                        cur.close()

                    # month
                    # 初回のみ初期値として0を29日間分入れる+今日の結果
                    if db_lis[i3][5] == 'None':
                        none_month = '0,0,0,0,' * 29
                        count_month = '%s%s,%s,%s,%s,' % (none_month, ave_day_person, ave_day_bicycle, ave_day_car, ave_day_motorcycle)
                        cur = conn.cursor(buffered=True)
                        sql = ("UPDATE spots SET spots_month = %s WHERE id = %s")
                        param = (count_month, db_lis[i3][0])
                        cur.execute(sql, param)
                        conn.commit()
                        cur.close()
                    else:
                        all_month = db_lis[i3][5].split(',')
                        del all_month[0:5]
                        count_month = '%s%s,%s,%s,%s,' % (all_month,ave_day_person, ave_day_bicycle, ave_day_car, ave_day_motorcycle)
                        cur = conn.cursor(buffered=True)
                        sql = ("UPDATE spots SET spots_week = %s WHERE id = %s")
                        param = (count_month, db_lis[i3][0])
                        cur.execute(sql, param)
                        conn.commit()
                        cur.close()

                else:
                    count_day = '%s%s,%s,%s,%s,' % (db_lis[i3][3], detect_lis[i3][0], detect_lis[i3][1], detect_lis[i3][2], detect_lis[i3][3])
                    cur = conn.cursor(buffered=True)
                    sql = ("UPDATE spots SET spots_day = %s WHERE id = %s")
                    param2 = (count_day,db_lis[i3][0])
                    cur.execute(sql,param2)
                    conn.commit()
                    cur.close()

        # １時間に1回更新（検出時間があるため正確ではない）
        sleep(3600)
# リストの変換用
def convert_1d_to_2d(l, cols):
    return [l[i:i + cols] for i in range(0, len(l), cols)]

@app.get("/detect")
def proc1():
    print(count)
    global response_lis
    # もしcountが0の時関数を起動（最初の一回のみ）
    if count == 0:
        asyncio.new_event_loop().run_in_executor(None, save_frame_camera_cycle)
    return response_lis

    

