"""
百人一首クイズアプリケーションのデータモデル定義
"""
from typing import List, Dict, Optional, Literal
from dataclasses import dataclass, field
from enum import Enum


class QuizMode(Enum):
    """出題モードの定義"""
    SEQUENTIAL = "sequential"  # 順番モード
    RANDOM = "random"          # ランダムモード


class QuestionType(Enum):
    """問題タイプの定義"""
    LOWER_MATCH = "lower_match"        # 下の句当て
    UPPER_MATCH = "upper_match"        # 上の句当て
    AUTHOR_MATCH = "author_match"      # 作者当て
    POEM_BY_AUTHOR = "poem_by_author"  # 作者から歌当て


# 問題パターンの定義
QUESTION_PATTERNS = {
    QuestionType.LOWER_MATCH.value: {
        "question": "次の上の句に続く下の句を選んでください：\n「{upper}」",
        "correct_field": "lower",
        "display_name": "下の句当て",
        "instruction": "上の句から正しい下の句を選択"
    },
    QuestionType.UPPER_MATCH.value: {
        "question": "次の下の句に対応する上の句を選んでください：\n「{lower}」",
        "correct_field": "upper",
        "display_name": "上の句当て",
        "instruction": "下の句から正しい上の句を選択"
    },
    QuestionType.AUTHOR_MATCH.value: {
        "question": "次の歌の作者を選んでください：\n「{upper}」\n「{lower}」",
        "correct_field": "author",
        "display_name": "作者当て",
        "instruction": "歌から正しい作者を選択"
    },
    QuestionType.POEM_BY_AUTHOR.value: {
        "question": "『{author}』の歌の下の句を選んでください",
        "correct_field": "lower",
        "display_name": "作者から歌当て",
        "instruction": "作者から正しい歌を選択"
    }
}


# UIカラー定義
COLORS = {
    "correct": "#4CAF50",      # 正解時の緑
    "incorrect": "#f44336",    # 不正解時の赤
    "selected": "#2196F3",     # 選択時の青
    "default": "#ffffff",      # デフォルト白
    "disabled": "#cccccc",     # 無効時のグレー
    "highlight": "#FFC107"     # ハイライト黄
}


@dataclass
class Question:
    """問題クラス"""
    poem_id: int                          # 歌のID
    question_type: str                    # 問題タイプ
    question_text: str                    # 問題文
    options: List[str]                    # 選択肢リスト（4択）
    correct_answer_index: int             # 正解のインデックス（0-3）
    poem_data: Dict                       # 元の歌データ
    question_number: Optional[int] = None # 問題番号（何問目か）
    
    def get_correct_answer(self) -> str:
        """正解の選択肢を取得"""
        return self.options[self.correct_answer_index]
    
    def check_answer(self, selected_index: int) -> bool:
        """回答が正解かチェック"""
        return selected_index == self.correct_answer_index
    
    def get_explanation(self) -> str:
        """解説文を生成"""
        poem = self.poem_data
        explanation = f"【第{poem['id']}首】\n"
        explanation += f"作者：{poem['author']}\n\n"
        explanation += f"上の句：{poem['upper']}\n"
        explanation += f"下の句：{poem['lower']}\n"
        
        # 読み仮名があれば追加
        if 'reading_upper' in poem and poem['reading_upper']:
            explanation += f"\n読み：\n"
            explanation += f"  {poem['reading_upper']}\n"
            explanation += f"  {poem['reading_lower']}\n"
        
        # 解説があれば追加
        if 'description' in poem and poem['description']:
            explanation += f"\n解説：\n{poem['description']}"
        
        return explanation


@dataclass
class QuizSession:
    """クイズセッション管理クラス"""
    quiz_mode: QuizMode = QuizMode.SEQUENTIAL           # 出題モード
    question_types: List[str] = field(default_factory=lambda: [QuestionType.LOWER_MATCH.value])
    current_question_index: int = 0                     # 現在の問題インデックス
    questions: List[Question] = field(default_factory=list)  # 問題リスト
    used_poem_ids: List[int] = field(default_factory=list)   # 使用済み歌ID
    score: int = 0                                      # 正解数
    total_answered: int = 0                             # 回答済み数
    current_answer: Optional[int] = None                # 現在の回答
    is_answered: bool = False                           # 回答済みフラグ
    max_questions: int = 100                            # 最大問題数
    
    def get_progress(self) -> str:
        """進捗状況を取得"""
        return f"{self.current_question_index + 1}/{self.max_questions}"
    
    def get_score_text(self) -> str:
        """スコアテキストを取得"""
        if self.total_answered == 0:
            return "スコア: 0/0 (0%)"
        accuracy = (self.score / self.total_answered) * 100
        return f"スコア: {self.score}/{self.total_answered} ({accuracy:.1f}%)"
    
    def add_question(self, question: Question) -> None:
        """問題を追加"""
        question.question_number = len(self.questions) + 1
        self.questions.append(question)
    
    def get_current_question(self) -> Optional[Question]:
        """現在の問題を取得"""
        if 0 <= self.current_question_index < len(self.questions):
            return self.questions[self.current_question_index]
        return None
    
    def submit_answer(self, selected_index: int) -> bool:
        """回答を送信"""
        if self.is_answered:
            return False
        
        self.current_answer = selected_index
        self.is_answered = True
        self.total_answered += 1
        
        question = self.get_current_question()
        if question and question.check_answer(selected_index):
            self.score += 1
            return True
        return False
    
    def next_question(self) -> bool:
        """次の問題に進む"""
        if self.current_question_index < len(self.questions) - 1:
            self.current_question_index += 1
            self.current_answer = None
            self.is_answered = False
            return True
        return False
    
    def reset(self) -> None:
        """セッションをリセット"""
        self.current_question_index = 0
        self.questions.clear()
        self.used_poem_ids.clear()
        self.score = 0
        self.total_answered = 0
        self.current_answer = None
        self.is_answered = False
    
    def is_completed(self) -> bool:
        """クイズが完了したかチェック"""
        return self.current_question_index >= self.max_questions - 1 and self.is_answered
    
    def get_statistics(self) -> Dict:
        """統計情報を取得"""
        stats = {
            "total_questions": len(self.questions),
            "answered": self.total_answered,
            "correct": self.score,
            "incorrect": self.total_answered - self.score,
            "accuracy": 0.0,
            "remaining": self.max_questions - self.total_answered
        }
        
        if self.total_answered > 0:
            stats["accuracy"] = (self.score / self.total_answered) * 100
        
        return stats


@dataclass
class QuizConfig:
    """クイズ設定クラス"""
    quiz_mode: QuizMode = QuizMode.SEQUENTIAL
    question_types: List[str] = field(default_factory=lambda: [
        QuestionType.LOWER_MATCH.value,
        QuestionType.UPPER_MATCH.value,
        QuestionType.AUTHOR_MATCH.value,
        QuestionType.POEM_BY_AUTHOR.value
    ])
    max_questions: int = 100
    show_reading: bool = True      # 読み仮名を表示
    show_description: bool = True  # 解説を表示
    time_limit: Optional[int] = None  # 制限時間（秒）、Noneは無制限
    
    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return {
            "quiz_mode": self.quiz_mode.value,
            "question_types": self.question_types,
            "max_questions": self.max_questions,
            "show_reading": self.show_reading,
            "show_description": self.show_description,
            "time_limit": self.time_limit
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'QuizConfig':
        """辞書から生成"""
        config = cls()
        if 'quiz_mode' in data:
            config.quiz_mode = QuizMode(data['quiz_mode'])
        if 'question_types' in data:
            config.question_types = data['question_types']
        if 'max_questions' in data:
            config.max_questions = data['max_questions']
        if 'show_reading' in data:
            config.show_reading = data['show_reading']
        if 'show_description' in data:
            config.show_description = data['show_description']
        if 'time_limit' in data:
            config.time_limit = data['time_limit']
        return config


# エラーメッセージ定義
ERROR_MESSAGES = {
    "FileNotFoundError": "データファイルが見つかりません",
    "JSONDecodeError": "データファイルの形式が不正です",
    "IndexError": "問題の生成に失敗しました",
    "KeyError": "データに必要な項目が不足しています",
    "ValueError": "入力値が不正です"
}


if __name__ == "__main__":
    # モデルの動作確認
    print("データモデル定義の確認")
    print("-" * 50)
    
    # QuizModeの確認
    print(f"出題モード: {[mode.value for mode in QuizMode]}")
    
    # QuestionTypeの確認
    print(f"問題タイプ: {[qtype.value for qtype in QuestionType]}")
    
    # 問題パターンの確認
    print("\n問題パターン:")
    for key, pattern in QUESTION_PATTERNS.items():
        print(f"  - {pattern['display_name']}: {pattern['instruction']}")
    
    # Questionクラスのテスト
    test_question = Question(
        poem_id=1,
        question_type=QuestionType.LOWER_MATCH.value,
        question_text="テスト問題",
        options=["選択肢1", "選択肢2", "選択肢3", "選択肢4"],
        correct_answer_index=0,
        poem_data={"id": 1, "author": "テスト作者", "upper": "上の句", "lower": "下の句"}
    )
    print(f"\nQuestionクラスのテスト: {test_question.check_answer(0)} (正解)")
    
    # QuizSessionクラスのテスト
    session = QuizSession()
    session.add_question(test_question)
    print(f"QuizSessionクラスのテスト: {session.get_progress()}")
    
    print("\n✅ データモデル定義完了")