from app import api


# test 用 spec ファイルを設定したら、ちゃんとそれが API として反映されるか

# 本番 spec に基づく API がちゃんと実行されるか
# @mock.path() で api の処理を mock する? ⇒ 内部ロジックが k8s sdk 読んでたりとかしてテストしづらいため、 spec がちゃんと読み込まれていることを期待値とする



if __name__ == '__main__':
    print()