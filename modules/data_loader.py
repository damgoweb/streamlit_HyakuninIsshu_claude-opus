"""
百人一首データの読み込みと管理を行うモジュール
"""
import json
import os
from typing import List, Dict, Optional
from pathlib import Path


class DataLoader:
    """百人一首データの読み込みと管理を行うクラス"""
    
    def __init__(self, json_path: str = "data/hyakunin_isshu.json"):
        """
        初期化
        
        Args:
            json_path: JSONファイルのパス
        """
        self.json_path = json_path
        self.data: List[Dict] = []
        self._load_and_validate_data()
    
    def _load_and_validate_data(self) -> None:
        """JSONファイルを読み込み、データを検証する"""
        try:
            # ファイルの存在確認
            if not os.path.exists(self.json_path):
                raise FileNotFoundError(f"データファイルが見つかりません: {self.json_path}")
            
            # JSONファイルの読み込み
            with open(self.json_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            
            # データ検証
            self._validate_data()
            
        except FileNotFoundError as e:
            raise FileNotFoundError(f"データファイルの読み込みエラー: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"JSONファイルの形式が不正です: {e}")
        except Exception as e:
            raise Exception(f"データ読み込み中に予期しないエラーが発生しました: {e}")
    
    def _validate_data(self) -> None:
        """読み込んだデータの妥当性を検証する"""
        required_fields = ['id', 'author', 'upper', 'lower']
        
        if not self.data:
            raise ValueError("データが空です")
        
        if not isinstance(self.data, list):
            raise ValueError("データはリスト形式である必要があります")
        
        # 100首あるか確認
        if len(self.data) != 100:
            print(f"警告: データ数が100首ではありません（{len(self.data)}首）")
        
        # 各歌のデータ検証
        for i, poem in enumerate(self.data):
            if not isinstance(poem, dict):
                raise ValueError(f"データ[{i}]が辞書形式ではありません")
            
            # 必須フィールドの確認
            for field in required_fields:
                if field not in poem:
                    raise KeyError(f"データ[{i}]に必須項目'{field}'が不足しています")
                if not poem[field]:
                    raise ValueError(f"データ[{i}]の'{field}'が空です")
            
            # IDの妥当性確認
            if not isinstance(poem['id'], int) or poem['id'] < 1 or poem['id'] > 100:
                raise ValueError(f"データ[{i}]のIDが不正です: {poem.get('id')}")
    
    def load_data(self) -> List[Dict]:
        """
        データを取得する
        
        Returns:
            百人一首データのリスト
        """
        return self.data.copy()
    
    def get_poem_by_id(self, poem_id: int) -> Optional[Dict]:
        """
        指定されたIDの歌を取得する
        
        Args:
            poem_id: 歌のID（1-100）
        
        Returns:
            歌のデータ（辞書）、見つからない場合はNone
        """
        for poem in self.data:
            if poem['id'] == poem_id:
                return poem.copy()
        return None
    
    def get_all_poems(self) -> List[Dict]:
        """
        全ての歌を取得する
        
        Returns:
            全ての歌のリスト
        """
        return self.data.copy()
    
    def get_poem_count(self) -> int:
        """
        歌の総数を取得する
        
        Returns:
            歌の総数
        """
        return len(self.data)
    
    def get_random_poems(self, count: int, exclude_id: Optional[int] = None) -> List[Dict]:
        """
        ランダムに歌を取得する
        
        Args:
            count: 取得する歌の数
            exclude_id: 除外する歌のID（オプション）
        
        Returns:
            ランダムに選ばれた歌のリスト
        """
        import random
        
        available_poems = [
            poem for poem in self.data 
            if exclude_id is None or poem['id'] != exclude_id
        ]
        
        if count > len(available_poems):
            count = len(available_poems)
        
        return random.sample(available_poems, count)
    
    def get_authors(self) -> List[str]:
        """
        全ての作者名を取得する
        
        Returns:
            作者名のリスト（重複なし）
        """
        return list(set(poem['author'] for poem in self.data))
    
    def get_poems_by_author(self, author: str) -> List[Dict]:
        """
        指定された作者の歌を取得する
        
        Args:
            author: 作者名
        
        Returns:
            該当する歌のリスト
        """
        return [poem.copy() for poem in self.data if poem['author'] == author]


# テスト用のメイン処理
if __name__ == "__main__":
    try:
        # データローダーのインスタンス作成
        loader = DataLoader()
        
        print(f"データ読み込み成功: {loader.get_poem_count()}首")
        
        # サンプルデータの表示
        sample_poem = loader.get_poem_by_id(1)
        if sample_poem:
            print(f"\n第1首のサンプル:")
            print(f"  作者: {sample_poem['author']}")
            print(f"  上の句: {sample_poem['upper']}")
            print(f"  下の句: {sample_poem['lower']}")
        
    except Exception as e:
        print(f"エラー: {e}")