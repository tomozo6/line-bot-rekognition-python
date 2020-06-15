# line-bot-rekognition-python
送信した画像を顔(感情)分析してくれるLINE BOTです。<br>
AWSのAPIGateway, Lambda(python), Rekognitionを使用して作成しています。<br>
また構築にはフレームワークである`AWS Chalice`を使用しています。<br>

## TL;DR;
```
$ git clone https://github.com/tomozo6/line-bot-rekognition-python.git
$ cd line-bot-rekognition-python
$ chalice deploy
```

## 構成図

![構成図](https://github.com/tomozo6/line-bot-rekognition-python/blob/master/doc/line-bot-rekognition-python.png)

この構成図のうち、AWSに関する部分が当Gitリポジトリの担当となります。
LINE関連の設定は含んでおりません。

## Prerequisites
- chalice 1.14.1
