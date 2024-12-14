## Local Testing
-- api_server周り 
---
* テスト用の環境変数を確認
    * variable.local.jsonの中身を確認し、必要であれば変更する
    * 現状、一部パラメータ確認用のみ存在

* pytest実行
    * pytest test_api_server.py --local
        * 対象テストがfailedにならず、passedになればよい
        * 警告は一旦無視で大丈夫

-- k8s_component周り
---
* pytest実行
   * pytest test_k8s_components.py
        * 対象テストがfailedにならず、passedになればよい

   * pytest test_has_completed_failed.py
        * 対象テストがfailedにならず、passedになればよい

   * pytest test_has_completed_exception.py
        * 対象テストがfailedにならず、passedになればよい