#原則このファイルに追加の処理を記述します。
import cv2
import os
import datetime
import shutil
import pafy
import subprocess
from subprocess import PIPE

#100フレーム枚に画像から検出を行い結果をリストで返す。
def save_frame_camera_cycle(device_num, dir_path, basename, cycle, ext='jpg', delay=1, window_name='frame'):
    video = pafy.new(device_num)
    best = video.getbest(preftype="mp4")
    cap = cv2.VideoCapture(best.url)
    
    if not cap.isOpened():
        return

    os.makedirs(dir_path, exist_ok=True)
    base_path = os.path.join(dir_path, basename)

    n = 0
    while True:
        ret, frame = cap.read()
        cv2.imshow(window_name, frame)
        if cv2.waitKey(delay) & 0xFF == ord('q'):
            break
        if n == cycle:
            n = 0
            cv2.imwrite('{}_{}.{}'.format(base_path, datetime.datetime.now().strftime('%Y%m%d%H%M%S%f'), ext), frame)
            proc = subprocess.run(['python', 'main.py'], stdout=PIPE, stderr=PIPE)
            proc_str = proc.stdout.decode('utf-8').split()
            proc_int = [int(s) for s in proc_str]
            #検出が終わった画像の削除
            target_dir = 'data/images/'
            shutil.rmtree(target_dir)
            os.mkdir(target_dir)
            shutil.rmtree('runs/detect/')
            #結果
            print(proc_int)
        n += 1

    cv2.destroyWindow(window_name)

#動画の入力。パスは後で変更する必要あるかも。
save_frame_camera_cycle('https://www.youtube.com/watch?v=3kPH7kTphnE', 'data/images', 'camera_capture_cycle', 100)