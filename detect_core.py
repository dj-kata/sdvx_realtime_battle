import numpy as np
from PIL import Image
import imagehash, os, imageio
import logging, logging.handlers
import sys

hash_onplay1  = imagehash.average_hash(Image.open('resources/onplay1.png'))
hash_onplay2  = imagehash.average_hash(Image.open('resources/onplay2.png'))
hash_onresult = imagehash.average_hash(Image.open('resources/onresult.png'))
#hash_is_select = imagehash.average_hash(Image.open('layout/is_select.png'))

# hash版
score_vals = [
    '1f3f43c3c3c2fcf8', # 0
    '1c3c0c0c0c0c0c0c', # 1
    '7e7f033b7f407f7f', # 2
    '7c7c023f7b037c78', # 3
    '1e3e46c6c6ffff06', # 4
    '7f7f404e5f037f7e', # 5
    '7c7ec0feffc3ff7e', # 6
    'fffe0e0c1c183030', # 7
    '3f7fc3ffffc3fffc', # 8
    '1e3f43c3ff033f3e', # 9
]
exscore_vals = [
    '7ec3c3c3c3c3c33e', # 0
    '0c0c0c0c0c0c0c0c', # 1
    '7f0303077e407f7f', # 2
    '7f0303071f037f7f', # 3
    '0b1b33637f7f0303', # 4
    '7f607c7f03037f7e', # 5
    'ffc0e0ffc3c3ff7e', # 6
    'ff0b03060c0c1818', # 7
    '7ec3c343ffc3eb7e', # 8
    '7fc3c3c37f0303ff', # 9
]

os.makedirs('log', exist_ok=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
hdl = logging.handlers.RotatingFileHandler(
    f'log/{os.path.basename(__file__).split(".")[0]}.log',
    encoding='utf-8',
    maxBytes=1024*1024*2,
    backupCount=1,
)

os.makedirs('log', exist_ok=True)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
hdl = logging.handlers.RotatingFileHandler(
    f'log/{os.path.basename(__file__).split(".")[0]}.log',
    encoding='utf-8',
    maxBytes=1024*1024*2,
    backupCount=1,
)
hdl.setLevel(logging.DEBUG)
hdl_formatter = logging.Formatter('%(asctime)s %(filename)s:%(lineno)5d %(funcName)s() [%(levelname)s] %(message)s')
hdl.setFormatter(hdl_formatter)
logger.addHandler(hdl)

def is_onplay(img):
    """現在の画面がプレー画面かどうか判定し、結果を返す

    Returns:
        bool: プレー画面かどうか
    """
    img1 = img.crop((0,420,130,507))
    tmp = imagehash.average_hash(img1)
    ret1 = abs(hash_onplay1 - tmp) < 10
    img2 = img.crop((15,876,310,891))
    tmp = imagehash.average_hash(img2)
    ret2 = abs(hash_onplay2 - tmp) < 10
    return ret1&ret2

def is_onresult(img):
    """現在の画面がリザルト画面かどうか判定し、結果を返す

    Returns:
        bool: リザルト画面かどうか
    """
    cr = img.crop((340,1600,539,1639))
    tmp = imagehash.average_hash(cr)
    val0 = abs(hash_onresult - tmp) <5 

    cr = img.crop((30,1390,239,1429))
    tmp = imagehash.average_hash(cr)
    img_j = Image.open('resources/onresult2.png')
    hash_target = imagehash.average_hash(img_j)
    val1 = abs(hash_target - tmp) < 5

    ret = val0 & val1
    return ret

### 選曲画面の終了判定
def detect_endselect(img):
    tmp = imagehash.average_hash(img.crop((0,0,1920,380)))
    img = Image.open('layout/endselect.png') #.crop((550,1,750,85))
    hash_target = imagehash.average_hash(img)
    ret = (hash_target - tmp) < 10
    return ret

### リザルト画面の終了判定
def detect_endresult(img):
    tmp = imagehash.average_hash(img)
    img2 = Image.open('layout/endresult.png')
    hash_target = imagehash.average_hash(img2)
    ret = (hash_target - tmp) < 10
    #logger.debug(f"ret = {ret}")
    return ret

# 最も近いdigitを検出
# 枠部分でプレー画面であることは保証できるはずなので、
# プレー画面中であれば少し精度を落としてもよいはず
def get_nearest(val:int, is_exscore=False):
    """入力された画素合計値に対し、最も近いdigitとそのときの合計値差分を返す

    Args:
        val (int): 画素合計値
        is_exscore (bool): EXスコア時にTrue

    Returns:
        minidx : 選択されたdigit
        mindiff: 合計値の差分
    """
    mindiff = 10000000000
    minidx = -1
    for i in range(10):
        #tmp = abs(score_vals[i]-val)
        if is_exscore:
            tmp = abs(imagehash.hex_to_hash(exscore_vals[i])-val)
        else:
            tmp = abs(imagehash.hex_to_hash(score_vals[i])-val)
        if tmp < mindiff:
            mindiff = tmp
            minidx = i
    return minidx, mindiff

def check_trans_screen(img):
    """切り替わり画面(ほぼ真っ黒)かどうかを判定

    Args:
        img (Image): ゲーム画面

    Returns:
        bool: 判定結果
    """
    ret = False
    val = np.array(img)[:,:,0-2].sum()
    ret = val < 2500000
    return ret

def get_score(img):
    """スコア部分を取得し、Noneまたはstrで返す

    Args:
        img (PIL.Image): ゲーム画面
        playside (str): 1p/2p/dp

    Returns:
        str: スコア('   0'とか' 137'とか)
    """
    ofsx = 0
    sy = 0

    ret = ''
    for i in range(4): # 上4桁
        sx = ofsx+52*i
        digit = img.crop((sx, sy, sx+47, sy+45))
        val = np.array(digit).sum()
        if val == 0: # 0は初期の000みたいな灰色の部分なので許容
            ret += ' '
        else:
            v,d = get_nearest(imagehash.average_hash(digit))
            if v in (5, 8): # 5,8を間違えるので対策
                if val>410000:
                    v=8
                else:
                    v=5
            ret += str(v)
    ofsx = 901-691
    sy = 406-396
    for i in range(4): # 下4桁
        sx = ofsx+41*i
        digit = img.crop((sx, sy, sx+36, sy+35))
        val = np.array(digit).sum()
        if val == 0: # 0は初期の000みたいな灰色の部分なので許容
            ret += ' '
        else:
            v,d = get_nearest(imagehash.average_hash(digit))
            if v in (5, 8): # 5,8を間違えるので対策
                if val>250000:
                    v=8
                else:
                    v=5
            ret += str(v)
    return ret

def get_exscore(img):
    """EXスコア部分を取得し、Noneまたはstrで返す

    Args:
        img (PIL.Image): ゲーム画面
        playside (str): 1p/2p/dp

    Returns:
        str: スコア('   0'とか' 137'とか)
    """
    ofsx = 931-691
    sy = 457-396
    dat = []

    ret = ''
    for i in range(5):
        sx = ofsx+16*i
        digit = img.crop((sx, sy, sx+13, sy+18))
        val = np.array(digit).sum()
        if val == 0: # 0は初期の000みたいな灰色の部分なので許容
            ret += ' '
        else:
            v,d = get_nearest(imagehash.average_hash(digit), True)
            ret += str(v)
    return ret

def get_rotate_img(img, top:int):
    """入力画像を90度回転して返す

    Args:
        img (Image): ゲーム画面
        top_is_right (bool, optional): 右に頭が来る場合True

    Returns:
        Image: 回転後のゲーム画面
    """
    ret = img
    if top==0:
        ret = img.rotate(90, expand=True)
    elif top == 2:
        ret = img.rotate(270, expand=True)
    return ret

def get_monochro_img(img, threshold=90):
    tmp = np.array(img.convert('L'), 'f')
    tmp_mono = (tmp>threshold)*255
    ret = Image.fromarray(np.uint8(tmp_mono))
    return ret

if __name__ == '__main__':
    import glob
    onplay = False
    sc = 0
    exsc = 0
    pre_sc = 0
    pre_exsc = 0
    for f in sys.argv[1:]:
        img = Image.open(f)
        img_rotate = get_rotate_img(img, 2)
        img_rotate.save('tmp.png')
        if onplay:
            if is_onresult(img_rotate):
                print('result!')
                onplay = False
                break
        #if is_onplay(img_rotate):
        onplay = True
        img_crop = img_rotate.crop((691,396,1080,475))
        mono = get_monochro_img(img_crop)
        #mono.save('mono.png')
        sc = get_score(mono)
        exsc = get_exscore(mono)
        if sc == '00000000':
            onplay = True
        if onplay:
            print(f"file:{f}, score:{sc}, EXscore:{exsc}")
            if type(pre_sc) == int and type(sc) == int:
                if (sc < pre_sc) or (exsc < pre_exsc):
                    print('error!')
                    break
                pre_sc = sc
                pre_exsc = exsc
