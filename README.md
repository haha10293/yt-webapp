# Web Video Downloader

`yt-dlp`を利用したYOUTUBE上の動画をダウンロードできるWebアプリケーションです。

フロントエンドにNext.js、バックエンドにFastAPIを使用し、Podmanコンテナ上で実行します。

## 使用技術

* Frontend  : Next.js
* Backend   : FastAPI
* pythonAPI : yt-dlp
* Container : Podman
* Web Server: nginx

---

# 利用上の注意

本アプリケーションを利用して動画をダウンロードする際は、以下の点に注意してください。

* ダウンロード対象のWebサービス・動画サイトの**利用規約を遵守してください**。
* 著作権法その他の法令に違反する目的で本アプリケーションを使用しないでください。
* ダウンロードした動画の利用・転載・再配布などについては、動画の権利者が定める条件に従ってください。
* 本アプリケーションは、利用者が適法に利用できる動画をダウンロードする目的で使用してください。
* 本アプリケーションの利用によって生じた問題について、開発者は責任を負いかねます。

---

## 動作環境

以下のいずれかの環境で動作します。

* Windows + WSL2
* macOS

アプリケーションの実行に必要なNode.js、Python、ffmpegなどはコンテナ内に用意するため、ホストOSへの個別インストールは基本的に不要です。

---

# Windows

## 1. WSL2の準備

WSL2が未導入の場合は、PowerShellを管理者権限で起動して以下を実行してください。

```powershell
wsl --install
```

インストール後、PCを再起動してください。

その後、WSL上のUbuntuなどを起動します。

以降の操作はWSLのターミナルで行ってください。

## 2. Podmanのインストール

Ubuntuの場合、以下を実行します。

```bash
sudo apt update
sudo apt install -y podman
```

インストール確認：

```bash
podman --version
```

## 3. Gitのインストール

Gitがインストールされていない場合は、以下を実行してください。

```bash
sudo apt install -y git
```

インストール確認：

```bash
git --version
```

## 4. リポジトリの取得

```bash
git clone <リポジトリURL>
cd yt-webapp
```

---

# macOS

## 1. Podmanのインストール

macOSではPodman公式インストーラの利用を推奨します。

以下の公式ページからmacOS版をインストールしてください。

[Podman公式インストールページ](https://podman.io/docs/installation?utm_source=chatgpt.com)

インストール確認：

```bash
podman --version
```

## 2. Podman machineの初期化

macOSでは、Linuxコンテナを実行するためにPodman machineを使用します。

初回のみ、以下を実行してください。

```bash
podman machine init
```

続けて起動します。

```bash
podman machine start
```

状態を確認：

```bash
podman machine list
```

`Running` と表示されていれば準備完了です。

### 次回以降

すでにPodman machineを作成済みの場合は、`init` は不要です。

```bash
podman machine start
```

だけで起動できます。

## 3. Gitの確認

macOSにはGitが標準で用意されている場合があります。

以下のコマンドで確認してください。

```bash
git --version
```


## 4. リポジトリの取得

```bash
git clone <リポジトリURL>
cd yt-webapp
```

---

# アプリケーションの起動

Windows・macOSともに、リポジトリのルートディレクトリで以下を実行します。

```bash
./start.sh
```

`start.sh` によって、以下の2つのコンテナがビルド・起動されます。

```text
downloader
    ↓
FastAPI / yt-dlp
    ↓
localhost:8000

nextjs
    ↓
Next.js / nginx
    ↓
localhost:3000
```

初回起動時はコンテナイメージのビルドが行われるため、完了まで時間がかかる場合があります。

起動後、ブラウザから以下にアクセスしてください。

```text
http://localhost:3000
```

---

# アプリケーションの利用方法

## 1. 動画URLを入力

入力欄に、ダウンロードしたい動画のURLを入力します。

URLを入力したら、**「抽出」ボタン**を押下します。

## 2. フォーマットを選択

動画データの形式の抽出が完了すると、**フォーマット選択のセレクトボックス**が表示されます。

セレクトボックスから、ダウンロードしたい形式を選択してください。

## 3. ダウンロード

形式を選択したら、**「ダウンロード」ボタン**を押下します。

ダウンロードが開始されます。

## 4. ダウンロード完了

ダウンロードが完了するまで待ちます。

---

# アプリケーションの停止

アプリケーションを停止する場合は、

```bash
./stop.sh
```

を実行してください。

`stop.sh` によって`nextjs`と`downloader`のコンテナを停止・削除します。

なお、コンテナを削除しても、ビルド済みのイメージは削除されません。

---

# macOSでPodman machineを停止する

macOSではPodman machineが起動している間、Linux VMが動作しています。

アプリケーションの使用が終わり、Podman自体も停止したい場合は、

```bash
podman machine stop
```

を実行してください。

次回使用するときは、

```bash
podman machine start
```

で再び起動できます。

Podman machineを停止しても、Podmanのイメージやファイルが削除されるわけではありません。

---

# よく使うPodmanコマンド

## コンテナの状態を確認

```bash
podman ps
```

停止中のコンテナも含めて確認：

```bash
podman ps -a
```

## イメージの一覧

```bash
podman images
```

## コンテナのログを確認

```bash
podman logs <コンテナ名>
```

## イメージを削除

```bash
podman rmi <イメージ名>
```

不要なイメージをまとめて削除する場合：

```bash
podman image prune
```

---

# ホスト環境について

本アプリケーションでは、実行に必要なソフトウェアをコンテナ内にまとめています。

そのため、以下のソフトウェアをホストOSに個別にインストールする必要はありません。

* Node.js
* Python
* ffmpeg
* nginx
* yt-dlp

また、Composeを使用せず、`start.sh` / `stop.sh`から直接Podmanコンテナを操作する構成にしています。

そのため、`podman-compose`やDocker Desktopなどを別途インストールする必要はありません。
