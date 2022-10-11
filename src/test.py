#原則このファイルに追加の処理を記述します。
import cv2
import os
import datetime
import shutil
import pafy
import subprocess
from subprocess import PIPE
from fastapi import FastAPI
app = FastAPI()

@app.get("/detect")
#動画から画像をキャプチャを生成して検出を行い結果をリストで返す。
def save_frame_camera_cycle():
    dir_path = 'yolov5_metaverse/data/images'
    basename = 'camera_capture_cycle'
    ext = 'jpg'

    #結果を保存するリスト、レスポンス用リスト（json）、URLを保存するリスト（データベースの実装後に改修する）
    delect_lis = []
    response_lis = []
    url_lis = [['渋谷スクランブル交差点','https://www.youtube.com/watch?v=3kPH7kTphnE'],['歌舞伎町一番街','https://www.youtube.com/watch?v=DjdUEyjx8GM']]

    for i in range(len(url_lis)):
        video = pafy.new(url_lis[i][1])
        best = video.getbest(preftype="mp4")
        cap = cv2.VideoCapture(best.url)
        if not cap.isOpened():
            return
        os.makedirs(dir_path, exist_ok=True)
        base_path = os.path.join(dir_path, basename)

        ret, frame = cap.read()
        cv2.imwrite('{}_{}.{}'.format(base_path, datetime.datetime.now().strftime('%Y%m%d%H%M%S%f'), ext), frame)
        proc = subprocess.run(['python', 'yolov5_metaverse/main.py','--nosave'], stdout=PIPE, stderr=PIPE)
        proc_str = proc.stdout.decode('utf-8').split()
        proc_int = [int(s) for s in proc_str]
        #検出が終わった画像の削除(要望があれば画像のパス返す処理を追加します)
        target_dir = 'yolov5_metaverse/data/images/'
        shutil.rmtree(target_dir)
        os.mkdir(target_dir)
        print(i)
        print(proc_int)
        delect_lis.append(proc_int)
    #shutil.rmtree('yolov5_metaverse/runs/detect/')

    for i2 in range(len(delect_lis)):
        data = {
            'name' : url_lis[i2][0],
            'person' : delect_lis[i2][0],
            'bicycle' : delect_lis[i2][1],
            'car' : delect_lis[i2][2]
        }
        response_lis.append(data)
    print(delect_lis)

    return response_lis

#動画の入力。パスは後で変更する必要あるかも。    