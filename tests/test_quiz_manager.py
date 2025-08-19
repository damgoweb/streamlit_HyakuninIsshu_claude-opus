"""
QuizManagerクラスのユニットテスト
"""
import unittest
import sys
import os
from pathlib import Path
from collections import Counter

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.quiz_manager import QuizManager
from modules.data_loader import DataLoader
from modules.models import (
    QuizMode, QuestionType, QUESTION_PATTERNS, QuizConfig, QuizSession
)


class TestQuizManager(unittest.TestCase):
    """QuizManagerクラスのテストケース"""
    
    @classmethod
    def setUpClass(cls):
        """テストクラスの初期化（一度だけ実行）"""
        cls.loader = DataLoader()
        cls.manager = QuizManager(cls.loader)
        
    def test_initialization(self):
        """初期化のテスト"""
        self.assertIsNotNone(self.manager)
        self.assertEqual(self.manager.poem_count, 100)
        print("✓ QuizManager初期化成功")
    
    def test_generate_question_all_types(self):
        """全問題タイプの生成テスト"""
        test_poem = self.loader.get_poem_by_id(1)
        
        for q_type in [QuestionType.LOWER_MATCH.value,
                      QuestionType.UPPER_MATCH.value,
                      QuestionType.AUTHOR_MATCH.value,
                      QuestionType.POEM_BY_AUTHOR.value]:
            
            with self.subTest(question_type=q_type):
                question = self.manager.generate_question(test_poem, q_type)
                
                # 基本的な検証
                self.assertIsNotNone(question)
                self.assertEqual(question.poem_id, 1)
                self.assertEqual(question.question_type, q_type)
                self.assertEqual(len(question.options), 4)
                
                # 正解が選択肢に含まれているか
                correct_answer = question.get_correct_answer()
                self.assertIn(correct_answer, question.options)
                
                print(f"✓ {QUESTION_PATTERNS[q_type]['display_name']}の生成成功")
    
    def test_no_duplicate_options(self):
        """選択肢の重複チェック"""
        # 100回テストして重複がないことを確認
        for i in range(100):
            poem = self.loader.get_poem_by_id((i % 100) + 1)
            question = self.manager.generate_question(
                poem, 
                QuestionType.LOWER_MATCH.value
            )
            
            # 選択肢に重複がないか確認
            self.assertEqual(len(question.options), len(set(question.options)),
                           f"選択肢に重複があります: {question.options}")
        
        print("✓ 100回のテストで選択肢の重複なし")
    
    def test_correct_answer_randomness(self):
        """正解位置のランダム性テスト"""
        positions = []
        test_count = 100
        
        # 同じ歌で複数回問題を生成
        test_poem = self.loader.get_poem_by_id(1)
        
        for _ in range(test_count):
            question = self.manager.generate_question(
                test_poem,
                QuestionType.LOWER_MATCH.value
            )
            positions.append(question.correct_answer_index)
        
        # 正解位置の分布を確認
        position_counts = Counter(positions)
        
        # 各位置（0-3）が少なくとも10%以上出現することを確認
        for position in range(4):
            count = position_counts.get(position, 0)
            percentage = (count / test_count) * 100
            self.assertGreater(percentage, 10,
                             f"位置{position}の出現率が低すぎます: {percentage:.1f}%")
        
        print(f"✓ 正解位置の分布: {dict(position_counts)}")
    
    def test_wrong_options_generation(self):
        """不正解選択肢生成のテスト"""
        test_poem = self.loader.get_poem_by_id(50)
        
        # 各問題タイプで不正解選択肢を生成
        for q_type in [QuestionType.LOWER_MATCH.value,
                      QuestionType.UPPER_MATCH.value,
                      QuestionType.AUTHOR_MATCH.value]:
            
            wrong_options = self.manager.get_wrong_options(test_poem, q_type, 3)
            
            # 3つの選択肢が生成されているか
            self.assertEqual(len(wrong_options), 3)
            
            # 正解が含まれていないか
            pattern = QUESTION_PATTERNS[q_type]
            correct_answer = test_poem[pattern['correct_field']]
            self.assertNotIn(correct_answer, wrong_options)
            
        print("✓ 不正解選択肢の生成成功")
    
    def test_sequential_mode(self):
        """順番モードのテスト"""
        config = QuizConfig(
            quiz_mode=QuizMode.SEQUENTIAL,
            question_types=[QuestionType.LOWER_MATCH.value],
            max_questions=10
        )
        
        session = self.manager.create_quiz_session(config)
        
        # 10問生成
        poem_ids = []
        for _ in range(10):
            question = self.manager.generate_next_question(session)
            if question:
                poem_ids.append(question.poem_id)
        
        # 順番通りか確認
        expected_ids = list(range(1, 11))
        self.assertEqual(poem_ids, expected_ids,
                        f"順番モードで歌IDが順番通りではありません: {poem_ids}")
        
        print(f"✓ 順番モード正常: {poem_ids}")
    
    def test_random_mode(self):
        """ランダムモードのテスト"""
        config = QuizConfig(
            quiz_mode=QuizMode.RANDOM,
            question_types=[QuestionType.LOWER_MATCH.value],
            max_questions=10
        )
        
        session = self.manager.create_quiz_session(config)
        
        # 10問生成
        poem_ids = []
        for _ in range(10):
            question = self.manager.generate_next_question(session)
            if question:
                poem_ids.append(question.poem_id)
        
        # 重複がないか確認
        self.assertEqual(len(poem_ids), len(set(poem_ids)),
                        f"ランダムモードで重複があります: {poem_ids}")
        
        # 完全に順番通りでないことを確認（偶然の一致を考慮）
        sequential = list(range(1, 11))
        if poem_ids == sequential:
            print("⚠ ランダムモードが偶然順番通りになりました（稀）")
        else:
            print(f"✓ ランダムモード正常: {poem_ids}")
    
    def test_session_management(self):
        """セッション管理のテスト"""
        config = QuizConfig(
            quiz_mode=QuizMode.SEQUENTIAL,
            question_types=[QuestionType.LOWER_MATCH.value],
            max_questions=5
        )
        
        session = self.manager.create_quiz_session(config)
        
        # 初期状態の確認
        self.assertEqual(session.score, 0)
        self.assertEqual(session.total_answered, 0)
        self.assertFalse(session.is_answered)
        
        # 問題を生成して回答
        question = self.manager.generate_next_question(session)
        self.assertIsNotNone(question)
        
        # 正解を送信
        is_correct = session.submit_answer(question.correct_answer_index)
        self.assertTrue(is_correct)
        self.assertEqual(session.score, 1)
        self.assertEqual(session.total_answered, 1)
        
        print("✓ セッション管理正常")
    
    def test_edge_cases(self):
        """エッジケースのテスト"""
        
        # 不正な問題タイプ
        with self.assertRaises(ValueError):
            test_poem = self.loader.get_poem_by_id(1)
            self.manager.generate_question(test_poem, "invalid_type")
        
        # 存在しない歌ID
        session = QuizSession()
        session.used_poem_ids = list(range(1, 101))  # 全て使用済み
        next_poem = self.manager.get_next_poem(
            QuizMode.RANDOM,
            100,
            session.used_poem_ids
        )
        self.assertIsNone(next_poem)
        
        print("✓ エッジケースの処理正常")
    
    def test_question_text_formatting(self):
        """問題文のフォーマットテスト"""
        test_poem = self.loader.get_poem_by_id(1)
        
        for q_type, pattern in QUESTION_PATTERNS.items():
            question = self.manager.generate_question(test_poem, q_type)
            
            # 問題文が空でないか
            self.assertTrue(len(question.question_text) > 0)
            
            # 問題文に歌の内容が含まれているか確認
            if q_type == QuestionType.LOWER_MATCH.value:
                self.assertIn(test_poem['upper'], question.question_text)
            elif q_type == QuestionType.UPPER_MATCH.value:
                self.assertIn(test_poem['lower'], question.question_text)
            elif q_type == QuestionType.AUTHOR_MATCH.value:
                self.assertIn(test_poem['upper'], question.question_text)
                self.assertIn(test_poem['lower'], question.question_text)
            elif q_type == QuestionType.POEM_BY_AUTHOR.value:
                self.assertIn(test_poem['author'], question.question_text)
        
        print("✓ 問題文フォーマット正常")


def run_tests():
    """テストを実行する"""
    print("=" * 50)
    print("QuizManagerクラスのテスト開始")
    print("=" * 50)
    
    # テストスイートの作成
    suite = unittest.TestLoader().loadTestsFromTestCase(TestQuizManager)
    
    # テストの実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ 全てのテストが成功しました！")
        print(f"実行: {result.testsRun}件")
    else:
        print(f"❌ テストに失敗しました")
        print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}件")
        print(f"失敗: {len(result.failures)}件")
        print(f"エラー: {len(result.errors)}件")
    print("=" * 50)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()