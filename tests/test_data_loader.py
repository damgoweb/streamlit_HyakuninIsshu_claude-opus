"""
DataLoaderクラスのユニットテスト
"""
import unittest
import sys
import os
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.data_loader import DataLoader


class TestDataLoader(unittest.TestCase):
    """DataLoaderクラスのテストケース"""
    
    def setUp(self):
        """各テストの前処理"""
        self.loader = None
        
    def test_data_loading_success(self):
        """正常なデータ読み込みのテスト"""
        try:
            self.loader = DataLoader()
            self.assertIsNotNone(self.loader.data)
            self.assertIsInstance(self.loader.data, list)
            print(f"✓ データ読み込み成功: {len(self.loader.data)}首")
        except Exception as e:
            self.fail(f"データ読み込みに失敗: {e}")
    
    def test_get_poem_by_id(self):
        """ID指定による歌取得のテスト"""
        self.loader = DataLoader()
        
        # 正常なID指定
        poem = self.loader.get_poem_by_id(1)
        self.assertIsNotNone(poem)
        self.assertEqual(poem['id'], 1)
        print(f"✓ ID=1の歌取得成功: {poem['author']}")
        
        # 存在しないID
        poem = self.loader.get_poem_by_id(999)
        self.assertIsNone(poem)
        print("✓ 存在しないIDの処理正常")
    
    def test_get_all_poems(self):
        """全歌取得のテスト"""
        self.loader = DataLoader()
        poems = self.loader.get_all_poems()
        
        self.assertIsInstance(poems, list)
        self.assertEqual(len(poems), self.loader.get_poem_count())
        print(f"✓ 全歌取得成功: {len(poems)}首")
    
    def test_get_random_poems(self):
        """ランダム歌取得のテスト"""
        self.loader = DataLoader()
        
        # 3首をランダムに取得
        random_poems = self.loader.get_random_poems(3)
        self.assertEqual(len(random_poems), 3)
        
        # IDを除外して取得
        random_poems_exclude = self.loader.get_random_poems(3, exclude_id=1)
        ids = [poem['id'] for poem in random_poems_exclude]
        self.assertNotIn(1, ids)
        print(f"✓ ランダム取得成功: {len(random_poems)}首")
    
    def test_data_validation(self):
        """データ検証のテスト"""
        self.loader = DataLoader()
        
        # 必須フィールドの確認
        required_fields = ['id', 'author', 'upper', 'lower']
        for poem in self.loader.data[:5]:  # 最初の5首をテスト
            for field in required_fields:
                self.assertIn(field, poem)
                self.assertIsNotNone(poem[field])
        
        print("✓ データ検証成功")
    
    def test_get_authors(self):
        """作者一覧取得のテスト"""
        self.loader = DataLoader()
        authors = self.loader.get_authors()
        
        self.assertIsInstance(authors, list)
        self.assertGreater(len(authors), 0)
        print(f"✓ 作者一覧取得成功: {len(authors)}人")
    
    def test_get_poems_by_author(self):
        """作者別歌取得のテスト"""
        self.loader = DataLoader()
        
        # 最初の歌の作者で検索
        first_poem = self.loader.get_poem_by_id(1)
        if first_poem:
            author = first_poem['author']
            poems = self.loader.get_poems_by_author(author)
            
            self.assertIsInstance(poems, list)
            self.assertGreater(len(poems), 0)
            
            # 取得した歌が全て同じ作者か確認
            for poem in poems:
                self.assertEqual(poem['author'], author)
            
            print(f"✓ 作者「{author}」の歌取得成功: {len(poems)}首")


def run_tests():
    """テストを実行する"""
    print("=" * 50)
    print("DataLoaderクラスのテスト開始")
    print("=" * 50)
    
    # テストスイートの作成
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDataLoader)
    
    # テストの実行
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ 全てのテストが成功しました！")
    else:
        print(f"❌ テストに失敗しました: {len(result.failures)}件の失敗、{len(result.errors)}件のエラー")
    print("=" * 50)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()