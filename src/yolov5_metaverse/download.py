import urllib.request as req
# URLや保存ファイル名を指定
url = 'https://www.jma.go.jp/bosai/forecast/data/forecast/010000.json'
filename = 'tenki.json'
# ダウンロード
req.urlretrieve(url, filename)