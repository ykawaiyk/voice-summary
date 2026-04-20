# 音声文字起こし＆要約プロジェクト

## ワークフロー

1. `recordings/` に音声ファイルを配置（mp3/m4a/wav/flac等）
2. `python transcribe.py` で文字起こし → `transcripts/` に `.txt` として出力
3. ユーザーが「要約して」と指示したら、`transcripts/` 内の未処理ファイルを規定フォーマットで要約し、`summaries/<元ファイル名>_summary.md` として保存

## 要約フォーマット（議事録形式）

要約は必ず以下のフォーマットで出力すること：

```
# [タイトル（音声ファイル名または内容から推定）]

## 基本情報
- 日時：（音声内容から推定、不明な場合は「不明」）
- 参加者：（発言者から推定）
- 議題：

## 要点（3〜5項目）
- 
- 

## 決定事項
- 

## ToDo
- [ ] 内容 / 担当：〇〇 / 期限：〇月〇日

## 次回予定
```

## 要約時のルール

- タイムスタンプ `[MM:SS]` は参考情報として使うが、要約本文には含めない
- 決定事項・ToDoは箇条書きで明確に記載
- 発言者が不明な場合は「参加者」「Aさん」等で表記
- 聞き取り不明瞭な箇所は `[不明瞭]` と明記
- `summaries/` に同名ファイルが既にある場合はスキップしてユーザーに確認
- 保存先のファイル名は `YYYYMMDD_HHMMSS_[内容を表す簡潔な名前].md` の形式にする
  - 例：`20260416_181516_ピョーさん面談_カフェ転職希望.md`
  - 例：`20260416_091030_〇〇社打ち合わせ_契約更新.md`
  - 日付・時刻は元ファイル名から取得する

## hamideru-app へのサマリー登録とアーカイブ

面談サマリーを hamideru-app に登録したら、そのファイルを `summaries/archive/` フォルダに移動すること。
これにより「まだ登録していないサマリー」と「登録済みサマリー」を一目で区別できる。

### 手順
1. `getCandidates` で候補者IDを特定する
2. `addInterviewSummary` で登録する
3. 登録成功を確認したら、ファイルを archive に移動する

```bash
# 登録
node -e "const fs=require('fs');const content=fs.readFileSync('C:/dev/voice-summary/summaries/<ファイル名>.md','utf8');process.stdout.write(JSON.stringify({candidateId:'<ID>',title:'<タイトル>',content,source:'claude'}));" | node C:/dev/hamideru-app/tools/api.js addInterviewSummary

# 登録成功後にアーカイブへ移動
mv "C:/dev/voice-summary/summaries/<ファイル名>.md" "C:/dev/voice-summary/summaries/archive/"
```

- `summaries/` にあるファイル = 未登録（またはhamideru-app不要）
- `summaries/archive/` にあるファイル = hamideru-app に登録済み
