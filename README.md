# yolov5-fastapi
yolov5の検出結果を返すためのAPI  
・[メインコード(YOLOv5,FastAPI)](https://github.com/plateau-system/yolov5-fastapi/tree/main/src)
## ディレクトリ構成  
```
yolov5_test
　　│─　src(Pythonスクリプト)
　　│─　Dockerfile 
　　└─　docker-compose.yml 
```
  
## 環境構築
〇Dockerのインストール  
〇Pythonのインストール(自分は3.10を使用)  
〇Postmanのインストール(APIの開発テストをするツールです。各自使いたいツールで良いと思います。)
  
〇任意のディレクトリで以下のコマンドを順番に実行。  
1.リポジトリのクローン(GitHub Desktopでクローンしている場合は必要ありません)
```
git clone https://github.com/k-seminar/kamigame_yolov5.git
```
2.kamigame_yolov5ディレクトリに移動。
```
cd kamigame_yolov5(ブランチによって名前が変わるかも)
```
3.Dockerのイメージをビルド
```
docker compose up -d --build
```
```
docker container exec -it plateau_system_python3 bash
```
4.YOLOv5のライブラリをインストール（必ずコンテナ内で行う）
```
cd src
```
```
pip install -r requirements.txt
```
5.注意点
恐らく99%の確立でビルドして最初にサーバーを起動すると正常に機能しません（エラーは出ないけどYOLOが動いていない状態になる）。
そこでpythonのライブラリを一部コメントアウトする必要がある。
```
↓2行をコメントアウト
 File "/usr/local/lib/python3.10/site-packages/pafy/backend_youtube_dl.py", line 53
 File "/usr/local/lib/python3.10/site-packages/pafy/backend_youtube_dl.py", line 54
```
6.srcに戻りPythonのAPIサーバーを起動（必ずコンテナ内で行う）
```
uvicorn api:app --host=0.0.0.0 --port=8090
```
7.終了コマンド
```
Ctrl + C
```
```
exit
```
  
## APIの仕様（初期案）
〇リクエストの頻度について
APIのレスポンスと検出実行の処理を非同期化しています。これによりいつでもレスポンスを提供できるようになりました。更新頻度は30秒+約10秒×地点数です（今後時刻指定にすることでタイムラグをゼロにする予定です）。
```
GET:http://0.0.0.0:8090/detect
```
```
[
 {
  "name": "渋谷スクランブル交差点",
  "person": 20,
  "bicycle": 0,
  "car": 2
 },
  {
  "name": "歌舞伎町一番街",
  "person": 10,
  "bicycle": 3,
  "car": 0
 },
]
```
