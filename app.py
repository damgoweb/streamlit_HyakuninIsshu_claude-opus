"""
百人一首クイズアプリケーション
Streamlitベースのインタラクティブな学習アプリ
"""
import streamlit as st
import sys
from pathlib import Path
import os
import datetime
import random

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from modules.data_loader import DataLoader
from modules.quiz_manager import QuizManager
from modules.models import (
    QuizMode, QuestionType, QUESTION_PATTERNS, 
    QuizConfig, QuizSession, COLORS
)


# 環境判別
def get_environment():
    """現在の環境（ブランチ）を取得"""
    # Streamlit CloudのSecretsから取得を試みる
    try:
        if 'BRANCH' in st.secrets:
            return st.secrets['BRANCH']
    except:
        pass
    
    # 環境変数から取得を試みる
    branch = os.environ.get('BRANCH', 'local')
    return branch


# ページ設定
st.set_page_config(
    page_title="百人一首クイズ",
    page_icon="🎌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 開発環境の表示
env = get_environment()
if env == 'develop':
    st.warning("⚠️ 開発環境 (develop branch)")
elif env == 'local':
    st.info("💻 ローカル環境")
# mainブランチの場合は何も表示しない


def init_session_state():
    """セッション状態の初期化"""
    if 'initialized' not in st.session_state:
        # データローダーとクイズマネージャーの初期化
        st.session_state.data_loader = DataLoader()
        st.session_state.quiz_manager = QuizManager(st.session_state.data_loader)
        
        # クイズ設定の初期化
        st.session_state.quiz_config = QuizConfig(
            quiz_mode=QuizMode.SEQUENTIAL,
            question_types=[QuestionType.LOWER_MATCH.value],
            max_questions=100
        )
        
        # セッション管理
        st.session_state.quiz_session = None
        st.session_state.current_question = None
        st.session_state.selected_answer = None
        st.session_state.is_answered = False
        st.session_state.show_explanation = False
        st.session_state.show_final_results = False  # 最終結果表示フラグ追加
        
        # 初期化完了フラグ
        st.session_state.initialized = True


def create_sidebar():
    """サイドバーの作成（設定エリア）"""
    with st.sidebar:
        # 環境表示
        env = get_environment()
        if env == 'develop':
            st.markdown("### 🔧 開発環境")
            st.caption("このバージョンはテスト中です")
            st.divider()
        
        st.title("⚙️ クイズ設定")
        
        # クイズが開始されているかチェック
        quiz_started = st.session_state.quiz_session is not None
        
        # 出題モード選択
        st.subheader("📝 出題モード")
        mode_options = {
            "sequential": "順番モード（1番から順に）",
            "random": "ランダムモード"
        }
        selected_mode = st.radio(
            "出題順序を選択",
            options=list(mode_options.keys()),
            format_func=lambda x: mode_options[x],
            index=0 if st.session_state.quiz_config.quiz_mode == QuizMode.SEQUENTIAL else 1,
            disabled=quiz_started,
            help="クイズ開始後は変更できません"
        )
        
        # 問題タイプ選択
        st.subheader("❓ 問題タイプ")
        question_type_options = {
            QuestionType.LOWER_MATCH.value: "下の句当て",
            QuestionType.UPPER_MATCH.value: "上の句当て",
            QuestionType.AUTHOR_MATCH.value: "作者当て",
            QuestionType.POEM_BY_AUTHOR.value: "作者から歌当て"
        }
        
        selected_types = st.multiselect(
            "出題する問題タイプを選択（複数可）",
            options=list(question_type_options.keys()),
            default=[QuestionType.LOWER_MATCH.value],
            format_func=lambda x: question_type_options[x],
            disabled=quiz_started,
            help="複数選択すると、ランダムに出題されます"
        )
        
        # 問題数設定
        st.subheader("🔢 問題数")
        max_questions = st.slider(
            "出題する問題数",
            min_value=5,
            max_value=100,
            value=10,
            step=5,
            disabled=quiz_started,
            help="最大100問まで設定可能"
        )
        
        # 設定を更新
        if not quiz_started:
            st.session_state.quiz_config.quiz_mode = QuizMode(selected_mode)
            st.session_state.quiz_config.question_types = selected_types if selected_types else [QuestionType.LOWER_MATCH.value]
            st.session_state.quiz_config.max_questions = max_questions
        
        st.divider()
        
        # クイズコントロール
        st.subheader("🎮 コントロール")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                "🚀 開始" if not quiz_started else "🔄 リセット",
                type="primary" if not quiz_started else "secondary",
                use_container_width=True
            ):
                start_or_reset_quiz()
        
        with col2:
            if st.button("📊 統計", use_container_width=True, disabled=not quiz_started):
                show_statistics()
        
        # 進捗表示
        if quiz_started and st.session_state.quiz_session:
            st.divider()
            st.subheader("📈 進捗状況")
            
            session = st.session_state.quiz_session
            # questionsリストの長さから実際の進捗を計算
            current_num = len(session.questions)
            progress = session.total_answered / session.max_questions if session.total_answered > 0 else 0
            
            st.progress(min(progress, 1.0))
            st.write(f"問題: {current_num}/{session.max_questions}")
            st.write(f"回答済み: {session.total_answered}問")
            st.write(f"{session.get_score_text()}")
            
            # 統計情報
            if session.total_answered > 0:
                accuracy = (session.score / session.total_answered) * 100
                if accuracy >= 80:
                    st.success(f"正答率: {accuracy:.1f}% 🎉")
                elif accuracy >= 60:
                    st.info(f"正答率: {accuracy:.1f}% 👍")
                else:
                    st.warning(f"正答率: {accuracy:.1f}% 💪")


def start_or_reset_quiz():
    """クイズを開始またはリセット"""
    # 最終結果表示フラグをリセット
    st.session_state.show_final_results = False
    
    # 新しいセッションを作成
    st.session_state.quiz_session = st.session_state.quiz_manager.create_quiz_session(
        st.session_state.quiz_config
    )
    
    # 最初の問題を生成
    question = st.session_state.quiz_manager.generate_next_question(
        st.session_state.quiz_session
    )
    st.session_state.current_question = question
    
    # 回答状態をリセット
    st.session_state.selected_answer = None
    st.session_state.is_answered = False
    st.session_state.show_explanation = False
    
    # ページを再描画
    st.rerun()


def show_statistics():
    """統計情報を表示"""
    if st.session_state.quiz_session:
        stats = st.session_state.quiz_session.get_statistics()
        st.sidebar.info(f"""
        📊 現在の統計:
        - 問題数: {len(st.session_state.quiz_session.questions)}問
        - 回答済み: {stats['answered']}問
        - 正解: {stats['correct']}問
        - 不正解: {stats['incorrect']}問
        - 正答率: {stats['accuracy']:.1f}%
        """)
        
        # デバッグ情報（開発時のみ）
        if st.sidebar.checkbox("デバッグ情報を表示", value=False):
            st.sidebar.write(f"total_answered: {st.session_state.quiz_session.total_answered}")
            st.sidebar.write(f"score: {st.session_state.quiz_session.score}")
            st.sidebar.write(f"is_answered: {st.session_state.quiz_session.is_answered}")
            st.sidebar.write(f"current_answer: {st.session_state.quiz_session.current_answer}")


def display_main_content():
    """メインコンテンツの表示"""
    # タイトルに環境情報を含める
    env = get_environment()
    if env == 'develop':
        st.title("🎌 百人一首クイズ [開発版]")
    else:
        st.title("🎌 百人一首クイズ")
    
    # 最終結果表示モードの場合
    if getattr(st.session_state, 'show_final_results', False):
        show_final_results()
    # クイズが開始されていない場合
    elif st.session_state.quiz_session is None:
        display_welcome_screen()
    else:
        display_quiz_screen()


def display_welcome_screen():
    """ウェルカム画面の表示"""
    st.markdown("""
    ### ようこそ！百人一首クイズへ
    
    このアプリは、百人一首を楽しく学べるクイズアプリケーションです。
    
    #### 📚 学習できること
    - **下の句当て**: 上の句から正しい下の句を選ぶ
    - **上の句当て**: 下の句から正しい上の句を選ぶ
    - **作者当て**: 歌から正しい作者を選ぶ
    - **作者から歌当て**: 作者名から正しい歌を選ぶ
    
    #### 🎯 遊び方
    1. 左側のサイドバーで設定を選択
    2. 「開始」ボタンをクリック
    3. 4択から正解を選んで「回答」ボタンをクリック
    4. 結果と解説を確認
    5. 「次の問題」で続ける
    
    #### 💡 ヒント
    - 順番モードは1番から順に出題されます
    - ランダムモードは毎回異なる順序で出題されます
    - 複数の問題タイプを選択すると、ランダムに出題されます
    
    **左のサイドバーから設定を選んで、「開始」ボタンを押してください！**
    """)
    
    # サンプル歌の表示
    st.divider()
    st.subheader("📖 今日の一首")
    
    # 日付ベースでランダムに選択（毎日異なる歌を表示）
    today = datetime.date.today()
    seed = int(today.strftime("%Y%m%d"))
    random.seed(seed)
    poem_id = random.randint(1, 100)
    
    # セッション状態で管理（リロードしても同じ歌を表示）
    if 'todays_poem_id' not in st.session_state:
        st.session_state.todays_poem_id = poem_id
    
    # 閲覧履歴を管理（オプション）
    if 'viewed_poem_ids' not in st.session_state:
        st.session_state.viewed_poem_ids = [st.session_state.todays_poem_id]
    
    sample_poem = st.session_state.data_loader.get_poem_by_id(st.session_state.todays_poem_id)
    
    if sample_poem:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info(f"""
            **第{sample_poem['id']}首**
            
            {sample_poem['upper']}  
            　　{sample_poem['lower']}
            
            **作者**: {sample_poem['author']}
            """)
        
        with col2:
            if 'reading_upper' in sample_poem:
                st.caption("読み")
                st.caption(f"{sample_poem['reading_upper']}")
                st.caption(f"{sample_poem['reading_lower']}")
            
            # リロードボタン（新しい歌を表示）
            remaining_poems = 100 - len(set(st.session_state.viewed_poem_ids))
            button_label = f"🔄 別の歌を見る (残り{remaining_poems}首)"
            
            # 全ての歌を見た場合はリセット
            if remaining_poems <= 0:
                if st.button("🔄 最初から見る", key="reset_poems"):
                    st.session_state.viewed_poem_ids = []
                    st.session_state.todays_poem_id = random.randint(1, 100)
                    st.rerun()
            else:
                if st.button(button_label, key="reload_poem"):
                    # まだ見ていない歌から選択
                    available_ids = [i for i in range(1, 101) if i not in st.session_state.viewed_poem_ids]
                    if available_ids:
                        new_poem_id = random.choice(available_ids)
                        st.session_state.todays_poem_id = new_poem_id
                        st.session_state.viewed_poem_ids.append(new_poem_id)
                        st.rerun()
            
            # 閲覧進捗の表示
            st.caption(f"閲覧済み: {len(set(st.session_state.viewed_poem_ids))}/100首")


def display_quiz_screen():
    """クイズ画面の表示"""
    if st.session_state.current_question is None:
        st.error("問題の生成に失敗しました")
        return
    
    question = st.session_state.current_question
    session = st.session_state.quiz_session
    
    # 問題番号と進捗
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        # 実際の問題番号を表示（questionsリストの長さから取得）
        current_num = len(session.questions)
        st.subheader(f"問題 {current_num}/{session.max_questions}")
    with col2:
        pattern = QUESTION_PATTERNS[question.question_type]
        st.info(f"📝 {pattern['display_name']}")
    with col3:
        if session.total_answered > 0:
            accuracy = (session.score / session.total_answered) * 100
            st.metric("正答率", f"{accuracy:.0f}%")
        else:
            st.metric("正答率", "-%")
    
    st.divider()
    
    # 問題文の表示
    st.markdown(f"### {question.question_text}")
    
    # 選択肢の表示
    st.subheader("選択肢")
    
    # 選択肢をラジオボタンで表示
    if not st.session_state.is_answered:
        st.session_state.selected_answer = st.radio(
            "答えを選んでください:",
            options=list(range(4)),
            format_func=lambda x: f"{x+1}. {question.options[x]}",
            key=f"question_{question.poem_id}_{question.question_type}",
            label_visibility="collapsed"
        )
    else:
        # 回答後は選択肢を色付きで表示
        for i, option in enumerate(question.options):
            if i == question.correct_answer_index:
                # 正解を緑で表示
                st.success(f"✅ {i+1}. {option}")
            elif i == st.session_state.selected_answer:
                # 選択した不正解を赤で表示
                st.error(f"❌ {i+1}. {option}")
            else:
                # その他の選択肢
                st.write(f"{i+1}. {option}")
    
    # ボタンエリア
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if not st.session_state.is_answered:
            if st.button("📝 回答", type="primary", use_container_width=True):
                submit_answer()
    
    with col2:
        if st.session_state.is_answered:
            # 最後の問題かチェック（生成済み問題数で判断）
            is_last = len(session.questions) >= session.max_questions
            
            if not is_last:
                if st.button("➡️ 次の問題", type="primary", use_container_width=True):
                    next_question()
            else:
                if st.button("🏁 結果を見る", type="primary", use_container_width=True):
                    # 結果表示モードに切り替え
                    st.session_state.show_final_results = True
                    st.rerun()
    
    # 結果と解説の表示
    if st.session_state.is_answered:
        display_result_and_explanation()


def submit_answer():
    """回答を送信"""
    if st.session_state.selected_answer is None:
        st.warning("選択肢を選んでください")
        return
    
    if st.session_state.is_answered:
        st.warning("既に回答済みです")
        return
    
    session = st.session_state.quiz_session
    question = st.session_state.current_question
    
    # 回答を記録
    st.session_state.is_answered = True
    session.is_answered = True
    session.total_answered += 1
    
    # 正誤判定
    if question.check_answer(st.session_state.selected_answer):
        session.score += 1
    
    st.session_state.show_explanation = True
    
    # ページを再描画
    st.rerun()


def next_question():
    """次の問題へ進む"""
    session = st.session_state.quiz_session
    
    # 問題数の上限チェック
    if len(session.questions) >= session.max_questions:
        st.warning("これ以上問題はありません")
        show_final_results()
        return
    
    # 新しい問題を生成
    question = st.session_state.quiz_manager.generate_next_question(session)
    
    if question:
        st.session_state.current_question = question
        # インデックスを進める
        session.current_question_index = len(session.questions) - 1
        
        # 回答状態をリセット（セッション全体のフラグもリセット）
        st.session_state.selected_answer = None
        st.session_state.is_answered = False
        st.session_state.show_explanation = False
        session.is_answered = False  # セッションのフラグもリセット
        session.current_answer = None
        
        # ページを再描画
        st.rerun()
    else:
        st.error("次の問題の生成に失敗しました")


def display_result_and_explanation():
    """結果と解説を表示"""
    question = st.session_state.current_question
    session = st.session_state.quiz_session
    
    st.divider()
    
    # 正誤の表示
    if st.session_state.selected_answer == question.correct_answer_index:
        st.success("🎉 正解です！")
    else:
        st.error(f"😢 不正解... 正解は「{question.get_correct_answer()}」でした")
    
    # 解説の表示
    with st.expander("📚 解説を見る", expanded=True):
        st.markdown(question.get_explanation())


def show_detailed_statistics():
    """詳細な統計情報を表示"""
    session = st.session_state.quiz_session
    if not session:
        return
    
    with st.expander("📊 詳細統計", expanded=True):
        # 問題タイプ別の統計
        stats = st.session_state.quiz_manager.get_question_statistics(session)
        
        st.markdown("#### 問題タイプ別成績")
        for q_type, count in stats['by_type'].items():
            pattern = QUESTION_PATTERNS[q_type]
            type_stats = stats['correct_by_type'][q_type]
            if type_stats['total'] > 0:
                accuracy = (type_stats['correct'] / type_stats['total']) * 100
                st.write(f"- {pattern['display_name']}: {type_stats['correct']}/{type_stats['total']} ({accuracy:.0f}%)")
        
        # セッション情報
        st.markdown("#### セッション情報")
        st.write(f"- 使用した問題ID: {session.used_poem_ids[:10]}..." if len(session.used_poem_ids) > 10 else f"- 使用した問題ID: {session.used_poem_ids}")
        st.write(f"- 出題モード: {'順番' if session.quiz_mode == QuizMode.SEQUENTIAL else 'ランダム'}")


def show_incorrect_questions():
    """間違えた問題を表示"""
    session = st.session_state.quiz_session
    if not session or not session.questions:
        return
    
    st.info("間違えた問題の復習機能は今後実装予定です")
    # TODO: 回答履歴を保存して、間違えた問題を表示する機能を実装


def show_final_results():
    """最終結果を表示"""
    session = st.session_state.quiz_session
    stats = session.get_statistics()
    
    st.balloons()
    
    st.divider()
    st.markdown("## 🏆 クイズ終了！")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("回答数", f"{stats['answered']}問")
    with col2:
        st.metric("正解数", f"{stats['correct']}問")
    with col3:
        st.metric("正答率", f"{stats['accuracy']:.1f}%")
    
    # 評価メッセージ
    if stats['accuracy'] >= 90:
        st.success("素晴らしい！百人一首マスターですね！🎉")
    elif stats['accuracy'] >= 70:
        st.info("よくできました！もう少しで完璧です！👍")
    elif stats['accuracy'] >= 50:
        st.warning("まずまずの成績です。もう一度挑戦してみましょう！💪")
    else:
        st.error("もっと練習が必要かもしれません。頑張りましょう！📚")
    
    # アクションボタンを追加
    st.divider()
    st.markdown("### 次のアクション")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 もう一度同じ設定で", type="primary", use_container_width=True):
            # 最終結果表示フラグをリセット
            st.session_state.show_final_results = False
            # 同じ設定で新しいクイズを開始
            start_or_reset_quiz()
    
    with col2:
        if st.button("⚙️ 設定を変更する", use_container_width=True):
            # 最終結果表示フラグをリセット
            st.session_state.show_final_results = False
            # セッションをクリアして初期画面に戻る
            st.session_state.quiz_session = None
            st.session_state.current_question = None
            st.session_state.selected_answer = None
            st.session_state.is_answered = False
            st.session_state.show_explanation = False
            st.rerun()
    
    with col3:
        if st.button("📊 詳細な統計を見る", use_container_width=True):
            show_detailed_statistics()
    
    # 間違えた問題の復習（オプション）
    if stats['incorrect'] > 0:
        st.divider()
        st.markdown("### 📝 間違えた問題の復習")
        if st.checkbox("間違えた問題を確認する"):
            show_incorrect_questions()


def main():
    """メイン処理"""
    # セッション状態の初期化
    init_session_state()
    
    # サイドバーの作成
    create_sidebar()
    
    # メインコンテンツの表示
    display_main_content()


if __name__ == "__main__":
    main()