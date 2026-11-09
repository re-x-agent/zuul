# 0002 Zuul の GitHub ドライバが読む topic の形: marker 方式（`topic:` ＋ ラベル値）、完全一致、接続ごとの option（2026-11-09）

状態: **確定**（user 決定。2026-11-09 18:18〜20:03 の一連の判断。最終形は 2026-11-09 19:53 の定義確定による）。
出典: `~/work-orders/zuul-topic-marker-rename.result.md`（最終形・名前の変更・定義確定）、`~/work-orders/zuul-topic-drop-prefix.result.md`（不採用の形の記録）、`~/work-orders/zuul-topic-exact-match.result.md`（完全一致の固定）、`~/work-orders/zuul-github-topic-proposal.draft.md`（Zuul への提案の下書き）。
関連: ADR 0001（Topic は GitHub のラベルで付与する、という決定 1）。この ADR は、その Topic を Zuul の GitHub ドライバがどう読むかを定める。

## 背景

- GitHub には topic の欄が無い。Gerrit にある topic（変更を束ねる属性）に相当するものが GitHub には無く、Zuul の GitHub ドライバは `Depends-On:` しか依存宣言を読めない。
- GitHub のラベルは**名前という1つの文字列だけ**である。「名前」と「値」に分かれた構造は GitHub には無い。したがって、ラベル `topic:release-1.4` を「`topic` という名前と `release-1.4` という値」と読むのは、**私たちのドライバの読み方の約束**であって、GitHub の仕様ではない。この約束を明示し、変えにくい形で固定する必要がある。

## 決定

### 1. 形は marker 方式（ラベル名＋セパレーター＋ラベル値）
- ラベルは「ラベル名＋セパレーター（`:`）＋ラベル値」と読む。**marker ＝ ラベル名＋セパレーター**（設定値は `topic:`）。
- topic は、marker の後ろの**ラベル値**（最初のセパレーターの後ろ、残り全部）。marker で始まらないラベルは topic ラベルではない。
- marker の照合は大小無視（GitHub のラベル名に合わせる）。値は元の綴りで保持する。

### 2. 照合は値の完全一致だけ
- 同じ topic かどうかは、ラベル値が**完全一致**するかどうかだけで決める。前方一致・部分一致・近さの段階は使わない。
- 理由: `1` と `11` が混ざってはいけない（前方一致だと `topic:1` の組に `topic:11` が入る）。一致したものがあるかどうかしか見ない、という単純さを保つ。
- 実装上の保証: Search の結果は、各 PR のラベルから topic を導出し直して要求した topic と完全一致するものだけ残す（Search 側が緩くても混ざらない）。

### 3. 設定は GitHub 接続ごとの option に置く
- `zuul.conf` の GitHub 接続節の `topic_label_marker`（既定なし＝無効）。有効化はこの option に加え、既存の queue の `dependencies-by-topic`（＋`allow-circular-dependencies`）。
- 理由: ラベルをどう読むかという約束は**接続（GitHub という外部の系）の境界に置くもの**で、テナントやジョブの設定ではない。同じ GitHub で同じ読み方が全テナントに及ぶ。

### 4. 用語は marker とする
- option 名は `topic_label_marker`、この仕組みを指す語は marker（設定値 `topic:` は、ラベル名＋セパレーター）。
- 理由: marker は、**ラベル名とラベル値の境目を示す目印**である、という実態をそのまま表す名前だから採用した。

## 採用しなかった案と理由

- **設定なし・ラベル名そのものが topic（共有ラベルで組になる）**: 実装とテスト（topic テスト 13/13 合格）まで進め、fork にも載せたが、不採用。どのラベル（例えば `bug`）でも組ができてしまい、意図しない PR 同士が1つの組として gate されるため。user が marker 方式へ戻す決定をした（2026-11-09 19:36）。
- **topic のラベル名を設定に列挙する形**: 不採用。設定に列挙したくないという user の意向（「設定はしたくない」）。
- **prefix という名前（「prefix」という呼び方）**: 採用しなかった。prefix は前方一致の照合を連想させ、照合が完全一致であるという実態と食い違う。「prefix なら前方一致で組になるのか」という誤解が繰り返し起きた。

## 帰結

- `topic:a:b` のラベル値は `a:b`（最初のセパレーターで割り、値は残り全部）。`topic:a` と `topic:a:b` は別の topic で組にならない。専用テスト（`test_topic_value_with_separator`）で固定済み。
- 番号の桁揃え（`topic:01` と `topic:1` を同じにしたい等）は**人側の注意**であって、機械の照合は表記によらず混ざらない（完全一致のため、別の値として扱われる）。
- 試行（`aether-zuul-01`）は `zuul-scheduler-topic:14.3.0-topic3` と `topic_label_marker=topic:` で稼働中。
- 残る論点（下書きの Open questions に記載）: 複数の topic ラベルを持つ PR（現状は辞書順で最小の1つを採用）、Search の反映遅延（実測 5.6〜10.7 秒、n=5）、待機中の組の増減時の再投入。

### 見通し（可能性の記録。実装の決定ではない）

- 区切りをセパレーターで持つ形にしたため、将来、**値の側に拡張の余地**が残る（例えば、1つのラベルが複数の値を持つマルチバリュー）。
- これは可能性の記録であって、**実装の決定ではない**。現行形は変わらず、「最初のセパレーターの後ろ全部が1つの値で、照合は完全一致」である（`topic:a:b` の値は `a:b`。値の中のセパレーターに特別な意味は無い）。拡張するかどうか、するならどの形かは、別途の決定とする。

## 証跡

- 実走検証: 2026-11-09 16:40、marker 方式の試作で、3 repo（web #24・mobile #563・resolver #124）の PR に同じ topic ラベルを付け、`gate_dev` が1つの組に合成して完走した（buildset `8882b07bf2b7496aa4610a983b79b243`）。当時の option 名は `topic_label_prefix`（改名のみで挙動不変）。
- fork（証跡用コピー、Zuul 14.3.0 基点）: https://github.com/re-x-agent/zuul/compare/14.3.0...topic-label-deps
- テスト: `tests/unit/test_github_topic.py`（topic テスト 14 件合格。`1` と `11`、緩い Search、値に `:` を含むラベル等）。
