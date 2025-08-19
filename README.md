# 百人一首クイズアプリ

百人一首を楽しく学べるWebベースのクイズアプリケーションです。Streamlitを使用して構築されています。

## 🎌 機能

### クイズモード
- **順番モード**: 1番から順番に出題
- **ランダムモード**: ランダムな順序で出題

### 問題タイプ
- **下の句当て**: 上の句から正しい下の句を選択
- **上の句当て**: 下の句から正しい上の句を選択
- **作者当て**: 歌から正しい作者を選択
- **作者から歌当て**: 作者名から正しい歌を選択

### その他の機能
- 4択問題形式
- リアルタイム正答率表示
- 詳細な解説表示
- 進捗管理
- 最終結果と評価

## 📦 インストール

### 必要要件
- Python 3.8以上
- pip

### セットアップ手順

1. リポジトリをクローン
```bash
git clone [your-repository-url]
cd hyakunin_isshu_quiz
```

2. 仮想環境を作成（推奨）
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

3. 依存ライブラリをインストール
```bash
pip install -r requirements.txt
```

## 🚀 使用方法

アプリケーションを起動:
```bash
streamlit run app.py
```

ブラウザが自動的に開き、`http://localhost:8501`でアプリケーションが表示されます。

## 📁 プロジェクト構成

```
hyakunin_isshu_quiz/
├── app.py                  # メインアプリケーション
├── data/
│   └── hyakunin_isshu.json # 百人一首データ
├── modules/
│   ├── data_loader.py      # データ読み込みモジュール
│   ├── quiz_manager.py     # クイズロジック管理
│   └── models.py           # データモデル定義
├── tests/                  # テストコード
│   ├── test_data_loader.py
│   └── test_quiz_manager.py
├── requirements.txt        # 依存ライブラリ
└── README.md              # このファイル
```

## 🧪 テスト

テストを実行:
```bash
# データローダーのテスト
python tests/test_data_loader.py

# クイズマネージャーのテスト
python tests/test_quiz_manager.py

# モジュールとして実行
python -m modules.data_loader
python -m modules.quiz_manager
python -m modules.models
```

## 📝 開発

### モジュール説明

- **data_loader.py**: JSONファイルから百人一首データを読み込み、管理
- **quiz_manager.py**: 問題生成、正誤判定、セッション管理
- **models.py**: Question、QuizSession等のデータモデル定義
- **app.py**: StreamlitによるWebインターフェース

### データ形式

`data/hyakunin_isshu.json`には以下の形式でデータが格納されています:
```json
{
    "id": 1,
    "author": "天智天皇",
    "upper": "秋の田の かりほの庵の 苫をあらみ",
    "lower": "わが衣手は 露にぬれつつ",
    "reading_upper": "あきのたの かりほのいほの とまをあらみ",
    "reading_lower": "わがころもでは つゆにぬれつつ",
    "description": "解説文..."
}
```

## 🤝 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容について議論してください。

## 📄 ライセンス

[ライセンスを選択してください - MIT, Apache 2.0, etc.]

## 👥 作者

[あなたの名前]

## 🙏 謝辞

- 百人一首のデータ提供元
- Streamlitコミュニティ