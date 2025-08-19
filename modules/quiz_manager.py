"""
百人一首クイズのロジック管理モジュール
"""
import random
import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

# インポート
from modules.models import (
    Question, QuizSession, QuizMode, QuestionType,
    QUESTION_PATTERNS, QuizConfig
)
from modules.data_loader import DataLoader


class QuizManager:
    """クイズのロジックを管理するクラス"""
    
    def __init__(self, data_loader: DataLoader):
        """
        初期化
        
        Args:
            data_loader: データローダーのインスタンス
        """
        self.data_loader = data_loader
        self.poems = data_loader.get_all_poems()
        self.poem_count = data_loader.get_poem_count()
        
    def generate_question(self, 
                         poem: Dict, 
                         question_type: str = QuestionType.LOWER_MATCH.value) -> Question:
        """
        指定された歌と問題タイプから問題を生成する
        
        Args:
            poem: 歌のデータ
            question_type: 問題タイプ
            
        Returns:
            生成された問題
        """
        # 問題パターンを取得
        pattern = QUESTION_PATTERNS.get(question_type)
        if not pattern:
            raise ValueError(f"不正な問題タイプ: {question_type}")
        
        # 問題文を生成
        question_text = self._format_question_text(poem, pattern['question'])
        
        # 正解を取得
        correct_answer = poem[pattern['correct_field']]
        
        # 不正解の選択肢を生成（3つ）
        wrong_options = self.get_wrong_options(poem, question_type, 3)
        
        # 選択肢を作成（正解＋不正解3つ）
        options = [correct_answer] + wrong_options
        
        # 選択肢をシャッフル
        random.shuffle(options)
        
        # 正解のインデックスを取得
        correct_answer_index = options.index(correct_answer)
        
        # Questionオブジェクトを作成
        question = Question(
            poem_id=poem['id'],
            question_type=question_type,
            question_text=question_text,
            options=options,
            correct_answer_index=correct_answer_index,
            poem_data=poem
        )
        
        return question
    
    def get_wrong_options(self, 
                         correct_poem: Dict, 
                         question_type: str, 
                         count: int = 3) -> List[str]:
        """
        不正解の選択肢を生成する
        
        Args:
            correct_poem: 正解の歌データ
            question_type: 問題タイプ
            count: 生成する選択肢の数
            
        Returns:
            不正解選択肢のリスト
        """
        pattern = QUESTION_PATTERNS.get(question_type)
        if not pattern:
            raise ValueError(f"不正な問題タイプ: {question_type}")
        
        field = pattern['correct_field']
        
        # 正解以外の歌から選択肢を抽出
        other_poems = [p for p in self.poems if p['id'] != correct_poem['id']]
        
        # 重複を避けるために選択肢を集合で管理
        wrong_options = set()
        
        # ランダムに選択
        random.shuffle(other_poems)
        
        for poem in other_poems:
            option = poem[field]
            # 正解と同じでなく、まだ追加されていない選択肢を追加
            if option != correct_poem[field] and option not in wrong_options:
                wrong_options.add(option)
                if len(wrong_options) >= count:
                    break
        
        # 必要数に満たない場合の処理（通常は発生しない）
        if len(wrong_options) < count:
            # 同じフィールドから重複を許可して追加
            for poem in other_poems:
                if len(wrong_options) >= count:
                    break
                wrong_options.add(poem[field])
        
        return list(wrong_options)[:count]
    
    def check_answer(self, question: Question, selected_index: int) -> bool:
        """
        回答が正解かチェックする
        
        Args:
            question: 問題
            selected_index: 選択されたインデックス
            
        Returns:
            正解の場合True
        """
        return question.check_answer(selected_index)
    
    def get_next_poem(self, 
                     mode: QuizMode, 
                     current_index: int, 
                     used_ids: List[int]) -> Optional[Dict]:
        """
        次の歌を取得する
        
        Args:
            mode: 出題モード
            current_index: 現在のインデックス
            used_ids: 使用済みID
            
        Returns:
            次の歌のデータ
        """
        if mode == QuizMode.SEQUENTIAL:
            # 順番モード
            next_id = current_index + 1
            if next_id > self.poem_count:
                return None
            return self.data_loader.get_poem_by_id(next_id)
        
        elif mode == QuizMode.RANDOM:
            # ランダムモード
            available_ids = [p['id'] for p in self.poems if p['id'] not in used_ids]
            if not available_ids:
                return None
            
            next_id = random.choice(available_ids)
            return self.data_loader.get_poem_by_id(next_id)
        
        return None
    
    def create_quiz_session(self, config: QuizConfig) -> QuizSession:
        """
        新しいクイズセッションを作成する
        
        Args:
            config: クイズ設定
            
        Returns:
            作成されたセッション
        """
        session = QuizSession(
            quiz_mode=config.quiz_mode,
            question_types=config.question_types,
            max_questions=min(config.max_questions, self.poem_count)
        )
        return session
    
    def generate_next_question(self, session: QuizSession) -> Optional[Question]:
        """
        セッションの次の問題を生成する
        
        Args:
            session: クイズセッション
            
        Returns:
            生成された問題、生成できない場合None
        """
        # 次の歌を取得
        if session.quiz_mode == QuizMode.SEQUENTIAL:
            next_poem = self.get_next_poem(
                session.quiz_mode,
                len(session.used_poem_ids),
                session.used_poem_ids
            )
        else:
            next_poem = self.get_next_poem(
                session.quiz_mode,
                session.current_question_index,
                session.used_poem_ids
            )
        
        if not next_poem:
            return None
        
        # 問題タイプをランダムに選択（複数タイプが設定されている場合）
        question_type = random.choice(session.question_types)
        
        # 問題を生成
        question = self.generate_question(next_poem, question_type)
        
        # セッションに追加
        session.used_poem_ids.append(next_poem['id'])
        session.add_question(question)
        
        return question
    
    def _format_question_text(self, poem: Dict, template: str) -> str:
        """
        問題文テンプレートをフォーマットする
        
        Args:
            poem: 歌データ
            template: 問題文テンプレート
            
        Returns:
            フォーマットされた問題文
        """
        return template.format(
            upper=poem.get('upper', ''),
            lower=poem.get('lower', ''),
            author=poem.get('author', ''),
            id=poem.get('id', '')
        )
    
    def get_question_statistics(self, session: QuizSession) -> Dict:
        """
        問題タイプ別の統計を取得
        
        Args:
            session: クイズセッション
            
        Returns:
            統計情報
        """
        stats = {
            'total': len(session.questions),
            'by_type': {},
            'correct_by_type': {}
        }
        
        # 問題タイプ別にカウント
        for question in session.questions:
            q_type = question.question_type
            if q_type not in stats['by_type']:
                stats['by_type'][q_type] = 0
                stats['correct_by_type'][q_type] = {'correct': 0, 'total': 0}
            
            stats['by_type'][q_type] += 1
            stats['correct_by_type'][q_type]['total'] += 1
            
            # 正解かどうかチェック（回答済みの場合）
            if session.is_answered and session.current_answer is not None:
                if question.check_answer(session.current_answer):
                    stats['correct_by_type'][q_type]['correct'] += 1
        
        return stats
    
    def get_random_question_type(self, available_types: List[str]) -> str:
        """
        利用可能な問題タイプからランダムに選択
        
        Args:
            available_types: 利用可能な問題タイプのリスト
            
        Returns:
            選択された問題タイプ
        """
        if not available_types:
            return QuestionType.LOWER_MATCH.value
        return random.choice(available_types)


# テスト用のメイン処理
if __name__ == "__main__":
    print("QuizManagerクラスのテスト")
    print("=" * 50)
    
    try:
        # データローダーとクイズマネージャーの初期化
        loader = DataLoader()
        manager = QuizManager(loader)
        
        print(f"✓ QuizManager初期化成功（{manager.poem_count}首）")
        
        # テスト用の歌を取得
        test_poem = loader.get_poem_by_id(1)
        
        # 各問題タイプでテスト
        print("\n問題生成テスト:")
        print("-" * 30)
        
        for q_type in [QuestionType.LOWER_MATCH.value, 
                      QuestionType.UPPER_MATCH.value,
                      QuestionType.AUTHOR_MATCH.value,
                      QuestionType.POEM_BY_AUTHOR.value]:
            
            # 問題を生成
            question = manager.generate_question(test_poem, q_type)
            
            # 問題情報を表示
            pattern = QUESTION_PATTERNS[q_type]
            print(f"\n【{pattern['display_name']}】")
            print(f"問題文: {question.question_text[:50]}...")
            print(f"選択肢数: {len(question.options)}")
            print(f"正解: {question.get_correct_answer()}")
            
            # 選択肢の重複チェック
            if len(question.options) == len(set(question.options)):
                print("✓ 選択肢に重複なし")
            else:
                print("✗ 選択肢に重複あり")
        
        # セッション作成テスト
        print("\n" + "=" * 50)
        print("セッション管理テスト:")
        print("-" * 30)
        
        config = QuizConfig(
            quiz_mode=QuizMode.SEQUENTIAL,
            question_types=[QuestionType.LOWER_MATCH.value],
            max_questions=5
        )
        
        session = manager.create_quiz_session(config)
        print(f"✓ セッション作成成功")
        
        # 5問生成してテスト
        for i in range(5):
            question = manager.generate_next_question(session)
            if question:
                print(f"  問題{i+1}: 歌番号{question.poem_id} - {QUESTION_PATTERNS[question.question_type]['display_name']}")
        
        print(f"\n使用済み歌ID: {session.used_poem_ids}")
        print(f"セッション進捗: {session.get_progress()}")
        
        print("\n" + "=" * 50)
        print("✅ QuizManagerクラスのテスト完了")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()