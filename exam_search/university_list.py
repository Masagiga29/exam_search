# 国公立大学リストサンプル
# このファイルを参考に、university_pastpaper_checker.py の test_universities を拡張できます

# 使い方: このリストをコピーして、スクリプト内の test_universities 辞書に追加

NATIONAL_UNIVERSITIES = {
    # 北海道・東北
    '北海道大学': 'https://www.hokudai.ac.jp/',
    '北海道教育大学': 'https://www.hokkyodai.ac.jp/',
    '室蘭工業大学': 'https://www.muroran-it.ac.jp/',
    '小樽商科大学': 'https://www.otaru-uc.ac.jp/',
    '帯広畜産大学': 'https://www.obihiro.ac.jp/',
    '旭川医科大学': 'https://www.asahikawa-med.ac.jp/',
    '北見工業大学': 'https://www.kitami-it.ac.jp/',
    '弘前大学': 'https://www.hirosaki-u.ac.jp/',
    '岩手大学': 'https://www.iwate-u.ac.jp/',
    '東北大学': 'https://www.tohoku.ac.jp/',
    '宮城教育大学': 'https://www.miyakyo-u.ac.jp/',
    '秋田大学': 'https://www.akita-u.ac.jp/',
    '山形大学': 'https://www.yamagata-u.ac.jp/',
    '福島大学': 'https://www.fukushima-u.ac.jp/',
    
    # 関東
    '茨城大学': 'https://www.ibaraki.ac.jp/',
    '筑波大学': 'https://www.tsukuba.ac.jp/',
    '筑波技術大学': 'https://www.tsukuba-tech.ac.jp/',
    '宇都宮大学': 'https://www.utsunomiya-u.ac.jp/',
    '群馬大学': 'https://www.gunma-u.ac.jp/',
    '埼玉大学': 'https://www.saitama-u.ac.jp/',
    '千葉大学': 'https://www.chiba-u.ac.jp/',
    '東京大学': 'https://www.u-tokyo.ac.jp/',
    '東京医科歯科大学': 'https://www.tmd.ac.jp/',
    '東京外国語大学': 'https://www.tufs.ac.jp/',
    '東京学芸大学': 'https://www.u-gakugei.ac.jp/',
    '東京農工大学': 'https://www.tuat.ac.jp/',
    '東京芸術大学': 'https://www.geidai.ac.jp/',
    '東京工業大学': 'https://www.titech.ac.jp/',
    '東京海洋大学': 'https://www.kaiyodai.ac.jp/',
    'お茶の水女子大学': 'https://www.ocha.ac.jp/',
    '電気通信大学': 'https://www.uec.ac.jp/',
    '一橋大学': 'https://www.hit-u.ac.jp/',
    '横浜国立大学': 'https://www.ynu.ac.jp/',
    
    # 中部
    '新潟大学': 'https://www.niigata-u.ac.jp/',
    '長岡技術科学大学': 'https://www.nagaokaut.ac.jp/',
    '上越教育大学': 'https://www.juen.ac.jp/',
    '富山大学': 'https://www.u-toyama.ac.jp/',
    '金沢大学': 'https://www.kanazawa-u.ac.jp/',
    '福井大学': 'https://www.u-fukui.ac.jp/',
    '山梨大学': 'https://www.yamanashi.ac.jp/',
    '信州大学': 'https://www.shinshu-u.ac.jp/',
    '岐阜大学': 'https://www.gifu-u.ac.jp/',
    '静岡大学': 'https://www.shizuoka.ac.jp/',
    '浜松医科大学': 'https://www.hama-med.ac.jp/',
    '名古屋大学': 'https://www.nagoya-u.ac.jp/',
    '愛知教育大学': 'https://www.aichi-edu.ac.jp/',
    '名古屋工業大学': 'https://www.nitech.ac.jp/',
    '豊橋技術科学大学': 'https://www.tut.ac.jp/',
    '三重大学': 'https://www.mie-u.ac.jp/',
    
    # 近畿
    '滋賀大学': 'https://www.shiga-u.ac.jp/',
    '滋賀医科大学': 'https://www.shiga-med.ac.jp/',
    '京都大学': 'https://www.kyoto-u.ac.jp/',
    '京都教育大学': 'https://www.kyokyo-u.ac.jp/',
    '京都工芸繊維大学': 'https://www.kit.ac.jp/',
    '大阪大学': 'https://www.osaka-u.ac.jp/',
    '大阪教育大学': 'https://osaka-kyoiku.ac.jp/',
    '兵庫教育大学': 'https://www.hyogo-u.ac.jp/',
    '神戸大学': 'https://www.kobe-u.ac.jp/',
    '奈良教育大学': 'https://www.nara-edu.ac.jp/',
    '奈良女子大学': 'https://www.nara-wu.ac.jp/',
    '和歌山大学': 'https://www.wakayama-u.ac.jp/',
    
    # 中国・四国
    '鳥取大学': 'https://www.tottori-u.ac.jp/',
    '島根大学': 'https://www.shimane-u.ac.jp/',
    '岡山大学': 'https://www.okayama-u.ac.jp/',
    '広島大学': 'https://www.hiroshima-u.ac.jp/',
    '山口大学': 'https://www.yamaguchi-u.ac.jp/',
    '徳島大学': 'https://www.tokushima-u.ac.jp/',
    '鳴門教育大学': 'https://www.naruto-u.ac.jp/',
    '香川大学': 'https://www.kagawa-u.ac.jp/',
    '愛媛大学': 'https://www.ehime-u.ac.jp/',
    '高知大学': 'https://www.kochi-u.ac.jp/',
    
    # 九州・沖縄
    '福岡教育大学': 'https://www.fukuoka-edu.ac.jp/',
    '九州大学': 'https://www.kyushu-u.ac.jp/',
    '九州工業大学': 'https://www.kyutech.ac.jp/',
    '佐賀大学': 'https://www.saga-u.ac.jp/',
    '長崎大学': 'https://www.nagasaki-u.ac.jp/',
    '熊本大学': 'https://www.kumamoto-u.ac.jp/',
    '大分大学': 'https://www.oita-u.ac.jp/',
    '宮崎大学': 'https://www.miyazaki-u.ac.jp/',
    '鹿児島大学': 'https://www.kagoshima-u.ac.jp/',
    '鹿屋体育大学': 'https://www.nifs-k.ac.jp/',
    '琉球大学': 'https://www.u-ryukyu.ac.jp/',
}

# 主な公立大学（一部）
PUBLIC_UNIVERSITIES = {
    '札幌医科大学': 'https://web.sapmed.ac.jp/',
    '釧路公立大学': 'https://www.kushiro-pu.ac.jp/',
    '公立はこだて未来大学': 'https://www.fun.ac.jp/',
    '青森県立保健大学': 'https://www.auhw.ac.jp/',
    '岩手県立大学': 'https://www.iwate-pu.ac.jp/',
    '宮城大学': 'https://www.myu.ac.jp/',
    '秋田県立大学': 'https://www.akita-pu.ac.jp/',
    '国際教養大学': 'https://web.aiu.ac.jp/',
    '会津大学': 'https://www.u-aizu.ac.jp/',
    '高崎経済大学': 'https://www.tcue.ac.jp/',
    '首都大学東京': 'https://www.tmu.ac.jp/',  # 現在は東京都立大学
    '横浜市立大学': 'https://www.yokohama-cu.ac.jp/',
    '富山県立大学': 'https://www.pu-toyama.ac.jp/',
    '石川県立大学': 'https://www.ishikawa-pu.ac.jp/',
    '福井県立大学': 'https://www.fpu.ac.jp/',
    '都留文科大学': 'https://www.tsuru.ac.jp/',
    '長野県立大学': 'https://www.u-nagano.ac.jp/',
    '岐阜薬科大学': 'https://www.gifu-pu.ac.jp/',
    '静岡県立大学': 'https://www.u-shizuoka-ken.ac.jp/',
    '愛知県立大学': 'https://www.aichi-pu.ac.jp/',
    '名古屋市立大学': 'https://www.nagoya-cu.ac.jp/',
    '三重県立看護大学': 'https://www.mcn.ac.jp/',
    '滋賀県立大学': 'https://www.usp.ac.jp/',
    '京都府立大学': 'https://www.kpu.ac.jp/',
    '京都府立医科大学': 'https://www.kpu-m.ac.jp/',
    '大阪公立大学': 'https://www.omu.ac.jp/',  # 大阪市立大学と大阪府立大学が統合
    '神戸市外国語大学': 'https://www.kobe-cufs.ac.jp/',
    '兵庫県立大学': 'https://www.u-hyogo.ac.jp/',
    '奈良県立医科大学': 'https://www.naramed-u.ac.jp/',
    '和歌山県立医科大学': 'https://www.wakayama-med.ac.jp/',
    '岡山県立大学': 'https://www.oka-pu.ac.jp/',
    '県立広島大学': 'https://www.pu-hiroshima.ac.jp/',
    '尾道市立大学': 'https://www.onomichi-u.ac.jp/',
    '下関市立大学': 'https://www.shimonoseki-cu.ac.jp/',
    '山口県立大学': 'https://www.yamaguchi-pu.ac.jp/',
    '香川県立保健医療大学': 'https://www.kagawa-puhs.ac.jp/',
    '愛媛県立医療技術大学': 'https://www.epu.ac.jp/',
    '高知県立大学': 'https://www.u-kochi.ac.jp/',
    '北九州市立大学': 'https://www.kitakyu-u.ac.jp/',
    '九州歯科大学': 'https://www.kyu-dent.ac.jp/',
    '福岡県立大学': 'https://www.fukuoka-pu.ac.jp/',
    '福岡女子大学': 'https://www.fwu.ac.jp/',
    '長崎県立大学': 'https://www.u-nagasaki.ac.jp/',
    '熊本県立大学': 'https://www.pu-kumamoto.ac.jp/',
    '大分県立看護科学大学': 'https://www.oita-nhs.ac.jp/',
    '宮崎県立看護大学': 'https://www.mpu.ac.jp/',
    '沖縄県立芸術大学': 'https://www.okigei.ac.jp/',
    '名桜大学': 'https://www.meio-u.ac.jp/',
}

# スクリプトで使用する際の例:
# checker.check_universities(NATIONAL_UNIVERSITIES)  # 国立大学全て
# checker.check_universities(PUBLIC_UNIVERSITIES)    # 公立大学
# または両方を結合
# all_universities = {**NATIONAL_UNIVERSITIES, **PUBLIC_UNIVERSITIES}
# checker.check_universities(all_universities)
