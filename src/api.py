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

#FastAPI(API)、count(初期動作のトリガー)、response_lis(初期値)
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
        cur.execute("SELECT spots_name, spots_url FROM spots")
        db_lis = cur.fetchall()
        print(db_lis[0])
        cur.close()

        #detect_lis(一時保存用)
        detect_lis = []
        #現在データベースが無いため仮の2次元リストに値を保存しています
        url_lis = [['渋谷スクランブル交差点','https://www.youtube.com/watch?v=3kPH7kTphnE'],['渋谷スクランブル交差点2','https://www.youtube.com/watch?v=3kPH7kTphnE']]
        
        if os.path.isdir('yolov5-plateau-system/runs/detect/'):
            shutil.rmtree('yolov5-plateau-system/runs/detect/')

        for i in range(len(db_lis)):
            video = pafy.new(db_lis[i][1])
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
            #検出が終わった画像の削除(要望があれば画像のパス返す処理を追加します)
            target_dir = 'yolov5-plateau-system/data/images/'
            shutil.rmtree(target_dir)
            os.mkdir(target_dir)
            detect_lis.append(proc_int)

        response_lis.clear()
        for i2 in range(len(detect_lis)):
            data = {
                'name' : db_lis[i2][0],
                'person' : detect_lis[i2][0],
                'bicycle' : detect_lis[i2][1],
                'car' : detect_lis[i2][2],
                'motorcycle' : detect_lis[i2][3]
            }
            response_lis.append(data)

        print(detect_lis)
        #30秒に1回更新（検出時間があるため正確ではない）
        sleep(30)

@app.get("/detect")
def proc1():
    print(count)
    global response_lis
    #もしcountが0の時関数を起動（最初の一回のみ）
    if count == 0:
        asyncio.new_event_loop().run_in_executor(None, save_frame_camera_cycle)
    return response_lis

    

