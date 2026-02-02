"""
クローラーのログ出力から大学名を抽出してデータベースに登録するDjango管理コマンド

使用方法:
    python manage.py import_universities_from_log

このコマンドは、リンク0〜322までの大学名を抽出して、
Universityモデルに登録します。
"""

import re
from django.core.management.base import BaseCommand
from django.db import transaction
from exams.models import University


class Command(BaseCommand):
    help = 'クローラーのログ出力から大学名を抽出してデータベースに登録します'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='データベースに保存せずに表示のみ'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run')

        # リンク0〜322のログデータ
        log_data = """リンク0: [東京大学] -> /new_kakomon_db/university/0l
リンク1: [京都大学] -> /new_kakomon_db/university/1c
リンク2: [北海道大学] -> /new_kakomon_db/university/01
リンク3: [東北大学] -> /new_kakomon_db/university/0a
リンク4: [名古屋大学] -> /new_kakomon_db/university/17
リンク5: [大阪大学] -> /new_kakomon_db/university/1f
リンク6: [九州大学] -> /new_kakomon_db/university/1x
リンク7: [東京科学大学] -> /new_kakomon_db/university/p5
リンク8: [一橋大学] -> /new_kakomon_db/university/0x
リンク9: [東京工業大学] -> /new_kakomon_db/university/0s
リンク10: [東京医科歯科大学(東京科学大学)] -> /new_kakomon_db/university/0m
リンク11: [大阪公立大学] -> /new_kakomon_db/university/le
リンク12: [岡山大学] -> /new_kakomon_db/university/1p
リンク13: [金沢大学] -> /new_kakomon_db/university/11
リンク14: [神戸大学] -> /new_kakomon_db/university/1i
リンク15: [埼玉大学] -> /new_kakomon_db/university/0j
リンク16: [静岡大学] -> /new_kakomon_db/university/16
リンク17: [東京都立大学] -> /new_kakomon_db/university/7q
リンク18: [信州大学] -> /new_kakomon_db/university/14
リンク19: [千葉大学] -> /new_kakomon_db/university/0k
リンク20: [筑波大学] -> /new_kakomon_db/university/0g
リンク21: [東京外国語大学] -> /new_kakomon_db/university/0n
リンク22: [広島大学] -> /new_kakomon_db/university/1q
リンク23: [横浜国立大学] -> /new_kakomon_db/university/0y
リンク24: [早稲田大学] -> /new_kakomon_db/university/bw
リンク25: [慶應義塾大学] -> /new_kakomon_db/university/9q
リンク26: [上智大学] -> /new_kakomon_db/university/9z
リンク27: [東京理科大学] -> /new_kakomon_db/university/b3
リンク28: [明治大学] -> /new_kakomon_db/university/bp
リンク29: [青山学院大学] -> /new_kakomon_db/university/9f
リンク30: [立教大学] -> /new_kakomon_db/university/bt
リンク31: [法政大学] -> /new_kakomon_db/university/bi
リンク32: [中央大学] -> /new_kakomon_db/university/ak
リンク33: [学習院大学] -> /new_kakomon_db/university/9k
リンク34: [関西学院大学] -> /new_kakomon_db/university/eg
リンク35: [関西大学] -> /new_kakomon_db/university/e2
リンク36: [同志社大学] -> /new_kakomon_db/university/df
リンク37: [立命館大学] -> /new_kakomon_db/university/dk
リンク38: [北海道大学] -> /new_kakomon_db/university/01
リンク39: [東北大学] -> /new_kakomon_db/university/0a
リンク40: [名古屋大学] -> /new_kakomon_db/university/17
リンク41: [京都大学] -> /new_kakomon_db/university/1c
リンク42: [大阪大学] -> /new_kakomon_db/university/1f
リンク43: [九州大学] -> /new_kakomon_db/university/1x
リンク44: [大阪市立大学] -> /new_kakomon_db/university/5i
リンク45: [岡山大学] -> /new_kakomon_db/university/1p
リンク46: [金沢大学] -> /new_kakomon_db/university/11
リンク47: [神戸大学] -> /new_kakomon_db/university/1i
リンク48: [熊本大学] -> /new_kakomon_db/university/22
リンク49: [信州大学] -> /new_kakomon_db/university/14
リンク50: [千葉大学] -> /new_kakomon_db/university/0k
リンク51: [筑波大学] -> /new_kakomon_db/university/0g
リンク52: [新潟大学] -> /new_kakomon_db/university/0z
リンク53: [広島大学] -> /new_kakomon_db/university/1q
リンク54: [三重大学] -> /new_kakomon_db/university/1a
リンク55: [旭川医科大学] -> /new_kakomon_db/university/06
リンク56: [札幌医科大学] -> /new_kakomon_db/university/51
リンク57: [福島県立医科大学] -> /new_kakomon_db/university/52
リンク58: [浜松医科大学] -> /new_kakomon_db/university/27
リンク59: [滋賀医科大学] -> /new_kakomon_db/university/28
リンク60: [京都府立医科大学] -> /new_kakomon_db/university/5g
リンク61: [和歌山県立医科大学] -> /new_kakomon_db/university/5o
リンク62: [奈良県立医科大学] -> /new_kakomon_db/university/5n
リンク63: [慶應義塾大学] -> /new_kakomon_db/university/9q
リンク64: [帝京大学] -> /new_kakomon_db/university/am
リンク65: [自治医科大学] -> /new_kakomon_db/university/8v
リンク66: [順天堂大学] -> /new_kakomon_db/university/9y
リンク67: [東京慈恵会医科大学] -> /new_kakomon_db/university/au
リンク68: [日本医科大学] -> /new_kakomon_db/university/b9
リンク69: [東邦大学] -> /new_kakomon_db/university/b4
リンク70: [日本大学] -> /new_kakomon_db/university/b8
リンク71: [近畿大学] -> /new_kakomon_db/university/e5
リンク72: [岩手医科大学] -> /new_kakomon_db/university/8g
リンク73: [東北医科薬科大学] -> /new_kakomon_db/university/8m
リンク74: [獨協医科大学] -> /new_kakomon_db/university/8w
リンク75: [金沢医科大学] -> /new_kakomon_db/university/ca
リンク76: [愛知医科大学] -> /new_kakomon_db/university/cm
リンク77: [大阪医科薬科大学] -> /new_kakomon_db/university/dm
リンク78: [関西医科大学] -> /new_kakomon_db/university/e3
リンク79: [兵庫医科大学] -> /new_kakomon_db/university/et
リンク80: [久留米大学] -> /new_kakomon_db/university/fo
リンク81: [産業医科大学] -> /new_kakomon_db/university/gq
リンク82: [防衛医科大学校] -> /new_kakomon_db/university/z5
リンク83: [藤田医科大学] -> /new_kakomon_db/university/d1
リンク84: [北海道大学] -> /new_kakomon_db/university/01
リンク85: [東北大学] -> /new_kakomon_db/university/0a
リンク86: [弘前大学] -> /new_kakomon_db/university/08
リンク87: [岩手大学] -> /new_kakomon_db/university/09
リンク88: [秋田大学] -> /new_kakomon_db/university/0c
リンク89: [福島大学] -> /new_kakomon_db/university/0e
リンク90: [帯広畜産大学] -> /new_kakomon_db/university/05
リンク91: [山形大学] -> /new_kakomon_db/university/0d
リンク92: [小樽商科大学] -> /new_kakomon_db/university/04
リンク93: [旭川医科大学] -> /new_kakomon_db/university/06
リンク94: [札幌医科大学] -> /new_kakomon_db/university/51
リンク95: [福島県立医科大学] -> /new_kakomon_db/university/52
リンク96: [秋田県立大学] -> /new_kakomon_db/university/7e
リンク97: [公立千歳科学技術大学] -> /new_kakomon_db/university/yp
リンク98: [室蘭工業大学] -> /new_kakomon_db/university/03
リンク99: [岩手県立大学] -> /new_kakomon_db/university/79
リンク100: [北海道教育大学] -> /new_kakomon_db/university/02
リンク101: [埼玉大学] -> /new_kakomon_db/university/0j
リンク102: [茨城大学] -> /new_kakomon_db/university/0f
リンク103: [宇都宮大学] -> /new_kakomon_db/university/0h
リンク104: [群馬大学] -> /new_kakomon_db/university/0i
リンク105: [千葉大学] -> /new_kakomon_db/university/0k
リンク106: [筑波大学] -> /new_kakomon_db/university/0g
リンク107: [東京大学] -> /new_kakomon_db/university/0l
リンク108: [東京科学大学] -> /new_kakomon_db/university/p5
リンク109: [一橋大学] -> /new_kakomon_db/university/0x
リンク110: [東京工業大学] -> /new_kakomon_db/university/0s
リンク111: [東京医科歯科大学(東京科学大学)] -> /new_kakomon_db/university/0m
リンク112: [東京都立大学] -> /new_kakomon_db/university/7q
リンク113: [横浜国立大学] -> /new_kakomon_db/university/0y
リンク114: [お茶の水女子大学] -> /new_kakomon_db/university/0v
リンク115: [東京外国語大学] -> /new_kakomon_db/university/0n
リンク116: [東京学芸大学] -> /new_kakomon_db/university/0o
リンク117: [東京藝術大学] -> /new_kakomon_db/university/0q
リンク118: [東京農工大学] -> /new_kakomon_db/university/0p
リンク119: [電気通信大学] -> /new_kakomon_db/university/0w
リンク120: [横浜市立大学] -> /new_kakomon_db/university/55
リンク121: [新潟大学] -> /new_kakomon_db/university/0z
リンク122: [信州大学] -> /new_kakomon_db/university/14
リンク123: [山梨大学] -> /new_kakomon_db/university/13
リンク124: [高崎経済大学] -> /new_kakomon_db/university/53
リンク125: [防衛大学校] -> /new_kakomon_db/university/z4
リンク126: [都留文科大学] -> /new_kakomon_db/university/57
リンク127: [公立諏訪東京理科大学] -> /new_kakomon_db/university/kn
リンク128: [長野県立大学] -> /new_kakomon_db/university/lw
リンク129: [新潟県立大学] -> /new_kakomon_db/university/lh
リンク130: [東京海洋大学] -> /new_kakomon_db/university/0t
リンク131: [防衛医科大学校] -> /new_kakomon_db/university/z5
リンク132: [上越教育大学] -> /new_kakomon_db/university/2h
リンク133: [静岡大学] -> /new_kakomon_db/university/16
リンク134: [岐阜大学] -> /new_kakomon_db/university/15
リンク135: [名古屋大学] -> /new_kakomon_db/university/17
リンク136: [金沢大学] -> /new_kakomon_db/university/11
リンク137: [富山大学] -> /new_kakomon_db/university/10
リンク138: [福井大学] -> /new_kakomon_db/university/12
リンク139: [愛知教育大学] -> /new_kakomon_db/university/18
リンク140: [名古屋工業大学] -> /new_kakomon_db/university/19
リンク141: [愛知県立大学] -> /new_kakomon_db/university/5b
リンク142: [名古屋市立大学] -> /new_kakomon_db/university/5d
リンク143: [福井県立大学] -> /new_kakomon_db/university/66
リンク144: [京都大学] -> /new_kakomon_db/university/1c
リンク145: [大阪大学] -> /new_kakomon_db/university/1f
リンク146: [大阪市立大学] -> /new_kakomon_db/university/5i
リンク147: [神戸大学] -> /new_kakomon_db/university/1i
リンク148: [奈良女子大学] -> /new_kakomon_db/university/1l
リンク149: [京都工芸繊維大学] -> /new_kakomon_db/university/1e
リンク150: [大阪教育大学] -> /new_kakomon_db/university/1h
リンク151: [奈良教育大学] -> /new_kakomon_db/university/1k
リンク152: [滋賀大学] -> /new_kakomon_db/university/1b
リンク153: [三重大学] -> /new_kakomon_db/university/1a
リンク154: [和歌山大学] -> /new_kakomon_db/university/1m
リンク155: [京都府立大学] -> /new_kakomon_db/university/5f
リンク156: [大阪府立大学] -> /new_kakomon_db/university/5j
リンク157: [神戸市外国語大学] -> /new_kakomon_db/university/5k
リンク158: [滋賀県立大学] -> /new_kakomon_db/university/73
リンク159: [兵庫県立大学] -> /new_kakomon_db/university/la
リンク160: [浜松医科大学] -> /new_kakomon_db/university/27
リンク161: [滋賀医科大学] -> /new_kakomon_db/university/28
リンク162: [京都府立医科大学] -> /new_kakomon_db/university/5g
リンク163: [和歌山県立医科大学] -> /new_kakomon_db/university/5o
リンク164: [奈良県立医科大学] -> /new_kakomon_db/university/5n
リンク165: [尾道市立大学] -> /new_kakomon_db/university/lz
リンク166: [岐阜薬科大学] -> /new_kakomon_db/university/58
リンク167: [静岡文化芸術大学] -> /new_kakomon_db/university/ml
リンク168: [公立小松大学] -> /new_kakomon_db/university/ls
リンク169: [富山県立大学] -> /new_kakomon_db/university/64
リンク170: [岡山大学] -> /new_kakomon_db/university/1p
リンク171: [広島大学] -> /new_kakomon_db/university/1q
リンク172: [鳥取大学] -> /new_kakomon_db/university/1n
リンク173: [島根大学] -> /new_kakomon_db/university/1o
リンク174: [山口大学] -> /new_kakomon_db/university/1r
リンク175: [県立広島大学] -> /new_kakomon_db/university/63
リンク176: [岡山県立大学] -> /new_kakomon_db/university/6b
リンク177: [広島市立大学] -> /new_kakomon_db/university/6e
リンク178: [徳島大学] -> /new_kakomon_db/university/1s
リンク179: [香川大学] -> /new_kakomon_db/university/1t
リンク180: [愛媛大学] -> /new_kakomon_db/university/1u
リンク181: [高知大学] -> /new_kakomon_db/university/1v
リンク182: [公立鳥取環境大学] -> /new_kakomon_db/university/kd
リンク183: [高知工科大学] -> /new_kakomon_db/university/yn
リンク184: [周南公立大学] -> /new_kakomon_db/university/fe
リンク185: [鳴門教育大学] -> /new_kakomon_db/university/2n
リンク186: [九州大学] -> /new_kakomon_db/university/1x
リンク187: [佐賀大学] -> /new_kakomon_db/university/20
リンク188: [長崎大学] -> /new_kakomon_db/university/21
リンク189: [熊本大学] -> /new_kakomon_db/university/22
リンク190: [大分大学] -> /new_kakomon_db/university/23
リンク191: [宮崎大学] -> /new_kakomon_db/university/24
リンク192: [鹿児島大学] -> /new_kakomon_db/university/25
リンク193: [琉球大学] -> /new_kakomon_db/university/26
リンク194: [下関市立大学] -> /new_kakomon_db/university/5q
リンク195: [福岡女子大学] -> /new_kakomon_db/university/5u
リンク196: [北九州市立大学] -> /new_kakomon_db/university/lc
リンク197: [福岡教育大学] -> /new_kakomon_db/university/1w
リンク198: [長崎県立大学] -> /new_kakomon_db/university/5v
リンク199: [熊本県立大学] -> /new_kakomon_db/university/5w
リンク200: [九州歯科大学] -> /new_kakomon_db/university/5t
リンク201: [宮崎公立大学] -> /new_kakomon_db/university/6c
リンク202: [北海学園大学] -> /new_kakomon_db/university/88
リンク203: [東北学院大学] -> /new_kakomon_db/university/8j
リンク204: [酪農学園大学] -> /new_kakomon_db/university/8b
リンク205: [東北芸術工科大学] -> /new_kakomon_db/university/ik
リンク206: [北海道情報大学] -> /new_kakomon_db/university/hz
リンク207: [北海道千歳リハビリテーション大学] -> /new_kakomon_db/university/l8
リンク208: [早稲田大学] -> /new_kakomon_db/university/bw
リンク209: [慶應義塾大学] -> /new_kakomon_db/university/9q
リンク210: [上智大学] -> /new_kakomon_db/university/9z
リンク211: [東京理科大学] -> /new_kakomon_db/university/b3
リンク212: [明治大学] -> /new_kakomon_db/university/bp
リンク213: [青山学院大学] -> /new_kakomon_db/university/9f
リンク214: [立教大学] -> /new_kakomon_db/university/bt
リンク215: [法政大学] -> /new_kakomon_db/university/bi
リンク216: [中央大学] -> /new_kakomon_db/university/ak
リンク217: [駒澤大学] -> /new_kakomon_db/university/9v
リンク218: [専修大学] -> /new_kakomon_db/university/ac
リンク219: [亜細亜大学] -> /new_kakomon_db/university/9g
リンク220: [学習院大学] -> /new_kakomon_db/university/9k
リンク221: [工学院大学] -> /new_kakomon_db/university/9r
リンク222: [國學院大学] -> /new_kakomon_db/university/9s
リンク223: [芝浦工業大学] -> /new_kakomon_db/university/9x
リンク224: [昭和女子大学] -> /new_kakomon_db/university/a1
リンク225: [成蹊大学] -> /new_kakomon_db/university/a7
リンク226: [成城大学] -> /new_kakomon_db/university/a8
リンク227: [獨協大学] -> /new_kakomon_db/university/94
リンク228: [神奈川大学] -> /new_kakomon_db/university/by
リンク229: [千葉工業大学] -> /new_kakomon_db/university/99
リンク230: [東海大学] -> /new_kakomon_db/university/an
リンク231: [東邦大学] -> /new_kakomon_db/university/b4
リンク232: [日本女子大学] -> /new_kakomon_db/university/bd
リンク233: [武蔵大学] -> /new_kakomon_db/university/bk
リンク234: [東京都市大学] -> /new_kakomon_db/university/ld
リンク235: [立正大学] -> /new_kakomon_db/university/bu
リンク236: [東京経済大学] -> /new_kakomon_db/university/as
リンク237: [東京電機大学] -> /new_kakomon_db/university/b0
リンク238: [東京農業大学] -> /new_kakomon_db/university/b1
リンク239: [北里大学] -> /new_kakomon_db/university/9l
リンク240: [国際基督教大学] -> /new_kakomon_db/university/9t
リンク241: [日本大学] -> /new_kakomon_db/university/b8
リンク242: [麻布大学] -> /new_kakomon_db/university/bx
リンク243: [帝京大学] -> /new_kakomon_db/university/am
リンク244: [昭和大学] -> /new_kakomon_db/university/a0
リンク245: [大東文化大学] -> /new_kakomon_db/university/af
リンク246: [武蔵野大学] -> /new_kakomon_db/university/bn
リンク247: [明治学院大学] -> /new_kakomon_db/university/bq
リンク248: [日本獣医生命科学大学] -> /new_kakomon_db/university/bc
リンク249: [創価大学] -> /new_kakomon_db/university/ad
リンク250: [茨城キリスト教大学] -> /new_kakomon_db/university/8s
リンク251: [植草学園大学] -> /new_kakomon_db/university/ns
リンク252: [鎌倉女子大学] -> /new_kakomon_db/university/c1
リンク253: [神田外語大学] -> /new_kakomon_db/university/he
リンク254: [関東学院大学] -> /new_kakomon_db/university/c0
リンク255: [関東学園大学] -> /new_kakomon_db/university/gh
リンク256: [群馬パース大学] -> /new_kakomon_db/university/ni
リンク257: [国士舘大学] -> /new_kakomon_db/university/9u
リンク258: [女子美術大学] -> /new_kakomon_db/university/a4
リンク259: [聖心女子大学] -> /new_kakomon_db/university/a9
リンク260: [聖路加国際大学] -> /new_kakomon_db/university/ab
リンク261: [多摩美術大学] -> /new_kakomon_db/university/aj
リンク262: [鶴見大学] -> /new_kakomon_db/university/c6
リンク263: [桐朋学園大学] -> /new_kakomon_db/university/b5
リンク264: [東京医療学院大学] -> /new_kakomon_db/university/n3
リンク265: [東京純心大学] -> /new_kakomon_db/university/yf
リンク266: [東京未来大学] -> /new_kakomon_db/university/nz
リンク267: [東京薬科大学] -> /new_kakomon_db/university/b2
リンク268: [新潟青陵大学] -> /new_kakomon_db/university/mj
リンク269: [文化学園大学] -> /new_kakomon_db/university/bh
リンク270: [横浜美術大学] -> /new_kakomon_db/university/n5
リンク271: [杏林大学] -> /new_kakomon_db/university/9o
リンク272: [聖マリアンナ医科大学] -> /new_kakomon_db/university/c4
リンク273: [獨協医科大学] -> /new_kakomon_db/university/8w
リンク274: [東京医科大学] -> /new_kakomon_db/university/ao
リンク275: [星薬科大学] -> /new_kakomon_db/university/bj
リンク276: [明治薬科大学] -> /new_kakomon_db/university/br
リンク277: [金沢工業大学] -> /new_kakomon_db/university/cc
リンク278: [中京大学] -> /new_kakomon_db/university/ct
リンク279: [南山大学] -> /new_kakomon_db/university/d2
リンク280: [名城大学] -> /new_kakomon_db/university/d4
リンク281: [神戸学院大学] -> /new_kakomon_db/university/el
リンク282: [同志社大学] -> /new_kakomon_db/university/df
リンク283: [関西大学] -> /new_kakomon_db/university/e2
リンク284: [関西学院大学] -> /new_kakomon_db/university/eg
リンク285: [京都産業大学] -> /new_kakomon_db/university/d9
リンク286: [京都女子大学] -> /new_kakomon_db/university/da
リンク287: [近畿大学] -> /new_kakomon_db/university/e5
リンク288: [甲南大学] -> /new_kakomon_db/university/ei
リンク289: [立命館大学] -> /new_kakomon_db/university/dk
リンク290: [武庫川女子大学] -> /new_kakomon_db/university/eu
リンク291: [佛教大学] -> /new_kakomon_db/university/dj
リンク292: [京都薬科大学] -> /new_kakomon_db/university/db
リンク293: [愛知学院大学] -> /new_kakomon_db/university/cn
リンク294: [大阪河﨑リハビリテーション大学] -> /new_kakomon_db/university/pc
リンク295: [大阪経済法科大学] -> /new_kakomon_db/university/dq
リンク296: [大阪工業大学] -> /new_kakomon_db/university/ds
リンク297: [大阪国際大学] -> /new_kakomon_db/university/e8
リンク298: [大阪物療大学] -> /new_kakomon_db/university/pg
リンク299: [京都光華女子大学] -> /new_kakomon_db/university/dc
リンク300: [京都美術工芸大学] -> /new_kakomon_db/university/o2
リンク301: [神戸芸術工科大学] -> /new_kakomon_db/university/i5
リンク302: [摂南大学] -> /new_kakomon_db/university/ge
リンク303: [常葉大学] -> /new_kakomon_db/university/op
リンク304: [豊田工業大学] -> /new_kakomon_db/university/h0
リンク305: [長浜バイオ大学] -> /new_kakomon_db/university/ox
リンク306: [名古屋外国語大学] -> /new_kakomon_db/university/ht
リンク307: [名古屋芸術大学] -> /new_kakomon_db/university/cy
リンク308: [阪南大学] -> /new_kakomon_db/university/eb
リンク309: [愛知大学] -> /new_kakomon_db/university/cl
リンク310: [愛知医科大学] -> /new_kakomon_db/university/cm
リンク311: [大阪医科薬科大学] -> /new_kakomon_db/university/dm
リンク312: [金沢医科大学] -> /new_kakomon_db/university/ca
リンク313: [関西外国語大学] -> /new_kakomon_db/university/e4
リンク314: [藤田医科大学] -> /new_kakomon_db/university/d1
リンク315: [広島修道大学] -> /new_kakomon_db/university/f9
リンク316: [川崎医療福祉大学] -> /new_kakomon_db/university/ij
リンク317: [高知健康科学大学] -> /new_kakomon_db/university/pw
リンク318: [広島国際大学] -> /new_kakomon_db/university/yy
リンク319: [九州産業大学] -> /new_kakomon_db/university/fm
リンク320: [西南学院大学] -> /new_kakomon_db/university/fp
リンク321: [福岡大学] -> /new_kakomon_db/university/fv
リンク322: [福岡歯科大学] -> /new_kakomon_db/university/fx"""

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('大学名抽出・登録ツール'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN モード: データベースには保存しません'))

        # 大学名を抽出
        self.stdout.write('\n1. ログデータから大学名を抽出中...')

        # 正規表現で大学名を抽出: リンクN: [大学名] -> URL
        pattern = r'リンク\d+: \[(.+?)\] -> '
        matches = re.findall(pattern, log_data)

        self.stdout.write(f'   {len(matches)}件のリンクを検出')

        # 重複を削除（順序を保持）
        unique_universities = []
        seen = set()
        for name in matches:
            if name not in seen:
                unique_universities.append(name)
                seen.add(name)

        self.stdout.write(f'   重複を削除: {len(unique_universities)}件のユニークな大学名')

        # 統計情報
        stats = {
            'created': 0,
            'existing': 0,
            'errors': 0
        }

        # データベースに登録
        self.stdout.write('\n2. データベースに登録中...')

        with transaction.atomic():
            for i, univ_name in enumerate(unique_universities, 1):
                try:
                    if not dry_run:
                        # 大学の取得または作成
                        university, created = University.objects.get_or_create(
                            name=univ_name,
                            defaults={
                                'school_type': 'university',
                            }
                        )

                        if created:
                            stats['created'] += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'   [{i}/{len(unique_universities)}] ✓ 新規作成: {univ_name}'
                                )
                            )
                        else:
                            stats['existing'] += 1
                            self.stdout.write(
                                f'   [{i}/{len(unique_universities)}] - 既存: {univ_name}'
                            )
                    else:
                        # DRY RUNモードでは既存チェックのみ
                        exists = University.objects.filter(name=univ_name).exists()
                        if exists:
                            stats['existing'] += 1
                            self.stdout.write(
                                f'   [{i}/{len(unique_universities)}] [DRY RUN] 既存: {univ_name}'
                            )
                        else:
                            stats['created'] += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'   [{i}/{len(unique_universities)}] [DRY RUN] 新規作成予定: {univ_name}'
                                )
                            )

                except Exception as e:
                    stats['errors'] += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'   [{i}/{len(unique_universities)}] ✗ エラー: {univ_name} - {e}'
                        )
                    )

        # 結果サマリーを表示
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('処理完了'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'総リンク数: {len(matches)}')
        self.stdout.write(f'ユニークな大学数: {len(unique_universities)}')
        self.stdout.write(f'新規作成: {stats["created"]}')
        self.stdout.write(f'既存: {stats["existing"]}')

        if stats['errors'] > 0:
            self.stdout.write(self.style.ERROR(f'エラー: {stats["errors"]}'))

        if not dry_run:
            self.stdout.write(self.style.SUCCESS('\nデータベースへの保存が完了しました'))
        else:
            self.stdout.write(self.style.WARNING('\nDRY RUN モードのため、データベースには保存されませんでした'))
            self.stdout.write('実際に登録するには、--dry-run オプションなしで実行してください')
