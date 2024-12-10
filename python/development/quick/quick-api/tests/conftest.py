import pytest
import os
import shutil

@pytest.fixture(autouse=True)
def test_output_dir():
    """テスト用出力ディレクトリの作成とクリーンアップ"""
    test_dir = os.path.join('output', 'test')
    os.makedirs(test_dir, exist_ok=True)
    yield test_dir
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)

@pytest.fixture
def mock_config():
    """テスト用の設定データ"""
    return {
        'api': {
            'base_url': 'https://test.api.quick-co.jp/octpath/v1/api',
            'access_key': 'test_key',
            'timeout': 30,
            'format': 'csv'
        },
        'retry': {
            'max_attempts': 2,
            'wait_seconds': 1.0
        },
        'endpoints': {
            'quote_index': {
                'path': 'quote_index',
                'description': 'テスト用エンドポイント'
            }
        }
    }