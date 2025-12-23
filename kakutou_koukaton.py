import pygame as pg
import sys
import os

# =====================
# 初期設定
# =====================
WIDTH, HEIGHT = 1000, 600
FLOOR = HEIGHT - 50

TITLE = 0
SELECT = 1
BATTLE = 2
PAUSED = 3
SETTINGS = 4

# OS判定して適切なフォントパスを設定
import platform
if platform.system() == "Windows":
    FONT_PATH = "C:/Windows/Fonts/msgothic.ttc"
elif platform.system() == "Darwin":  # macOS
    FONT_PATH = "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc"
else:  # Linux等
    FONT_PATH = None  # システムデフォルトフォントを使用

# BGMファイル(プロジェクト内の相対パス)
MENU_BGM = "sound/bgm/menu-bgm.mp3"
BATTLE_BGM = "sound/bgm/vhs-tape.mp3"

# マッチ時間(秒) -- 90秒
MATCH_TIME = 90

# カレントディレクトリをスクリプトの場所に
try:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
except Exception:
    pass

pg.init()
pg.mixer.init()
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("こうかとん ファイター")
clock = pg.time.Clock()

# フォント
FONT_BIG = pg.font.Font(None, 80)
FONT_MED = pg.font.Font(None, 36)
FONT_SMALL = pg.font.Font(None, 24)


# =====================
# ユーティリティ関数
# =====================
def safe_load_and_play_bgm(path, volume=0.5, loops=-1):
    """
    BGMを安全にロードして再生する(ファイルが無くてもクラッシュさせない)。
    """
    try:
        pg.mixer.music.load(path)
        pg.mixer.music.set_volume(volume)
        pg.mixer.music.play(loops)
    except Exception as e:
        print(f"[BGM load error] {path} : {e}")


# =====================
# 画像読み込み
# =====================
TITLE_BG = pg.transform.scale(
    pg.image.load("ダウンロード (1).jpg").convert(),
    (WIDTH, HEIGHT)
)

# =====================
# ステージ定義
# =====================
STAGES = [
    {
        "name": "境内",
        "bg": pg.transform.scale(
            pg.image.load("Tryfog.jpg").convert(),
            (WIDTH, HEIGHT)
        )
    },
    {
        "name": "稽古場",
        "bg": pg.transform.scale(
            pg.image.load("ダウンロード.jpg").convert(),
            (WIDTH, HEIGHT)
        )
    },
    {
        "name": "繁華街(夜)",
        "bg": pg.transform.scale(
            pg.image.load("3Dオリジナル背景作品 格闘ゲーム用背景.jpg").convert(),
            (WIDTH, HEIGHT)
        )
    }
]


# =====================
# Fighter クラス
# =====================
class Fighter(pg.sprite.Sprite):
    def __init__(self, x, keys, char_name):
        super().__init__()

        # ===== 画像 =====
        self.idle_r = pg.transform.scale(
            pg.image.load(f"fig/{char_name}fighter.png").convert_alpha(), (150, 200)
        )
        self.idle_l = pg.transform.flip(self.idle_r, True, False)

        self.punch_r = pg.transform.scale(
            pg.image.load(f"fig/{char_name}fighter_punch.png").convert_alpha(), (150, 200)
        )
        self.punch_l = pg.transform.flip(self.punch_r, True, False)

        self.kick_r = pg.transform.scale(
            pg.image.load(f"fig/{char_name}fighter_kick.png").convert_alpha(), (190, 200)
        )
        self.kick_l = pg.transform.flip(self.kick_r, True, False)

        self.image = self.idle_r
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (x, FLOOR)

        # ===== 本体 HurtBox（常時）=====
        self.hurtbox = pg.Rect(0, 0, 60, 180)
        self.update_hurtbox()

        # ===== 攻撃中の追加 HurtBox =====
        self.attack_hurtbox = None

        self.vx = 0
        self.vy = 0
        self.on_ground = True

        self.hp = 100

        self.keys = keys
        self.facing = 1

        self.attack_timer = 0
        self.recover_timer = 0

    def update_hurtbox(self):
        self.hurtbox.centerx = self.rect.centerx
        self.hurtbox.bottom = self.rect.bottom

    def update_attack_hurtbox(self):
        if self.attack_timer == 0:
            self.attack_hurtbox = None
            return

        # パンチ中
        if self.image in (self.punch_r, self.punch_l):
            w, h = 65, 30
            offset_x = 70 if self.facing == 1 else -70
            offset_y = 60

        # キック中
        elif self.image in (self.kick_r, self.kick_l):
            w, h = 85, 35
            offset_x = 70 if self.facing == 1 else -70
            offset_y = -60

        else:
            self.attack_hurtbox = None
            return

        self.attack_hurtbox = pg.Rect(0, 0, w, h)
        self.attack_hurtbox.centerx = self.rect.centerx + offset_x
        self.attack_hurtbox.centery = self.rect.centery - offset_y

    def update(self, key_lst):
        self.vx = 0
        can_move = (self.attack_timer == 0 and self.recover_timer == 0)

        if can_move:
            if key_lst[self.keys["left"]]:
                self.vx = -6
                self.facing = -1
            if key_lst[self.keys["right"]]:
                self.vx = 6
                self.facing = 1
            if key_lst[self.keys["jump"]] and self.on_ground:
                self.vy = -20
                self.on_ground = False

        if self.attack_timer > 0:
            self.attack_timer -= 1
            if self.attack_timer == 0:
                self.recover_timer = 20
        elif self.recover_timer > 0:
            self.recover_timer -= 1
        else:
            self.image = self.idle_r if self.facing == 1 else self.idle_l

        self.vy += 1
        self.rect.x += self.vx
        self.rect.y += self.vy

        if self.rect.bottom >= FLOOR:
            self.rect.bottom = FLOOR
            self.vy = 0
            self.on_ground = True
            
        # ===== ノックバック減衰 =====
        if self.knockback_vx != 0:
            self.knockback_vx *= 0.85  # 徐々に減速
            if abs(self.knockback_vx) < 0.5:
                self.knockback_vx = 0

    def do_attack(self, atk_type, attacks, hurtboxes, opponent):
        if self.attack_timer > 0 or self.recover_timer > 0:
            return

        if atk_type == "punch":
            self.image = self.punch_r if self.facing == 1 else self.punch_l
            self.attack_timer = 12
        else:
            self.image = self.kick_r if self.facing == 1 else self.kick_l
            self.attack_timer = 16

        attacks.add(Attack(self, atk_type))
        hurtboxes.add(HurtBox(opponent, atk_type))



        self.update_hurtbox()
        self.update_attack_hurtbox()

    def do_attack(self, atk_type, attacks):
        if self.attack_timer > 0 or self.recover_timer > 0:
            return

        if atk_type == "punch":
            self.image = self.punch_r if self.facing == 1 else self.punch_l
            self.attack_timer = 20
        elif atk_type == "kick":
            self.image = self.kick_r if self.facing == 1 else self.kick_l
            self.attack_timer = 30

        attacks.add(Attack(self, atk_type))

# =====================
# 攻撃クラス
# =====================
class Attack(pg.sprite.Sprite):
    DATA = {
        "punch": {"size": (40, 20), "life": 8, "damage": 5},
        "kick":  {"size": (65, 25), "life": 10, "damage": 8},
    }

    def __init__(self, fighter, atk_type):
        super().__init__()
        self.owner = fighter
        self.damage = self.DATA[atk_type]["damage"]

        w, h = self.DATA[atk_type]["size"]
        self.image = pg.Surface((w, h), pg.SRCALPHA)
        self.image.fill((255, 0, 0, 120))

        self.rect = self.image.get_rect()
        offset_x = 70 if fighter.facing == 1 else -70
        offset_y = 60 if atk_type == "punch" else -60

        self.rect.centerx = fighter.rect.centerx + offset_x
        self.rect.centery = fighter.rect.centery - offset_y

        self.life = self.DATA[atk_type]["life"]

    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.kill()
            

# =====================
# HPバー描画
# =====================
def draw_hp(screen, fighter, x):
    pg.draw.rect(screen, (255, 0, 0), (x, 20, 300, 20))
    pg.draw.rect(screen, (0, 255, 0), (x, 20, 3 * fighter.hp, 20))


# =====================
# ダメージ判定関数
# =====================
def check_damage(attacks, hurtboxes):
    """
    攻撃判定とくらい判定の衝突をチェックし、ダメージを適用する
    
    Args:
        attacks: 攻撃判定のスプライトグループ
        hurtboxes: くらい判定のスプライトグループ
    """
    for atk in attacks:
        for hb in hurtboxes:
            if atk.owner != hb.owner and atk.rect.colliderect(hb.rect):
                hb.owner.hp -= atk.damage
                apply_knockback(hb.owner, atk.owner, atk.damage)
                atk.kill()
                return  # 1フレームに1ヒットまで


# =====================
# UI: タイマー・スコア・ポーズ等を管理するクラス
# =====================
class HUD:
    """
    画面上部のタイマー・スコア・ポーズボタン・下部の操作説明を描画する。
    """
    def __init__(self):
        self.match_time = MATCH_TIME
        self.p1_wins = 0
        self.p2_wins = 0
        # ポーズボタン領域(右上)
        self.pause_rect = pg.Rect(WIDTH - 110, 70, 100, 40)
        # 音量
        self.volume = 0.5

# =====================
# HPバー
# =====================
def draw_hp(screen, fighter, x):
    pg.draw.rect(screen, (255, 0, 0), (x, 20, 300, 20))
    pg.draw.rect(screen, (0, 255, 0), (x, 20, 3 * fighter.hp, 20))

    def update_time(self, dt):
        """
        秒単位の時間を減少させる(dt は秒)。
        """
        self.match_time = max(0, self.match_time - dt)

    def draw_top(self, screen):
        """
        上部中央に時間、左/右にスコア、右上にポーズボタンを描画する。
        """
        # スコア(左・右)
        score_left = FONT_MED.render(f"P1 Wins: {self.p1_wins}", True, (255, 255, 255))
        score_right = FONT_MED.render(f"P2 Wins: {self.p2_wins}", True, (255, 255, 255))
        screen.blit(score_left, (10, 10))
        screen.blit(score_right, (WIDTH - 10 - score_right.get_width(), 10))

        # タイマー(中央) - 秒表示(整数)
        time_sec = int(self.match_time)

        # 30秒以下で点滅(偶数秒:赤 / 奇数秒:白)
        if time_sec <= 30 and time_sec % 2 == 0:
            time_color = (255, 0, 0)   # 赤
        else:
            time_color = (255, 255, 255)

        time_text = FONT_MED.render(f"Time: {time_sec}", True, time_color)
        screen.blit(time_text, (WIDTH // 2 - time_text.get_width() // 2, 10))

        # ポーズボタン(右上)
        pg.draw.rect(screen, (180, 180, 180), self.pause_rect)
        p_label = FONT_SMALL.render("PAUSE", True, (0, 0, 0))
        screen.blit(p_label, (self.pause_rect.centerx - p_label.get_width() // 2,
                              self.pause_rect.centery - p_label.get_height() // 2))

    def draw_bottom_controls(self, screen, p1_keys_text, p2_keys_text):
        """
        画面下部に1行で操作説明を表示(左側P1、右側P2)。
        """
        # 1行の背面灰色長方形(視認性のため)
        rect = pg.Rect(0, HEIGHT - 40, WIDTH, 40)
        pg.draw.rect(screen, (40, 40, 40), rect)
        left = FONT_SMALL.render(p1_keys_text, True, (220, 220, 220))
        right = FONT_SMALL.render(p2_keys_text, True, (220, 220, 220))
        screen.blit(left, (10, HEIGHT - 32))
        screen.blit(right, (WIDTH - 10 - right.get_width(), HEIGHT - 32))


# =====================
# UI: ポーズ画面。続行・設定・終了のメニュー
# =====================
class PauseMenu:
    """
    ポーズ画面。続行・設定・終了メニューを実装。
    """
    def __init__(self, hud):
        self.options = ["Continue", "Settings", "Quit"]
        self.selected = 0
        self.hud = hud

    def draw(self, screen):
        """
        半透明の背景+メニュー描画。
        """
        overlay = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        title = FONT_BIG.render("Paused", True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        # メニュー
        for i, opt in enumerate(self.options):
            color = (255, 255, 0) if i == self.selected else (220, 220, 220)
            label = FONT_MED.render(opt, True, color)
            rect = label.get_rect(center=(WIDTH // 2, 220 + i * 70))
            screen.blit(label, rect)

        # 操作ガイド
        guide = FONT_SMALL.render("↑↓ Select  ENTER Confirm  SPACE Continue", True, (200, 200, 200))
        screen.blit(guide, (WIDTH // 2 - guide.get_width() // 2, 500))

    def handle_event(self, event):
        """
        キー入力でメニューを操作する。選択確定は呼び出し元で判定する。
        """
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_UP:
                self.selected = (self.selected - 1) % len(self.options)
            if event.key == pg.K_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            if event.key == pg.K_RETURN:
                return self.options[self.selected]
            if event.key == pg.K_SPACE:
                return "Continue"
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            # クリックで選択
            mx, my = event.pos
            for i, opt in enumerate(self.options):
                label = FONT_MED.render(opt, True, (0, 0, 0))
                rect = label.get_rect(center=(WIDTH // 2, 220 + i * 70))
                if rect.collidepoint(mx, my):
                    return opt
        return None


# =====================
# UI: 設定画面(音量調整)
# =====================
class SettingsMenu:
    """
    設定画面(音量調整)。
    """
    def __init__(self, hud):
        self.hud = hud

    def draw(self, screen):
        """
        設定画面の描画。
        """
        overlay = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        title = FONT_BIG.render("Settings", True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        # 音量表示
        vol_text = FONT_MED.render(f"Music Volume: {int(self.hud.volume * 100)}%", True, (255, 255, 255))
        screen.blit(vol_text, (WIDTH // 2 - vol_text.get_width() // 2, 250))

        # 音量バー
        bar_back = pg.Rect(WIDTH // 2 - 150, 320, 300, 20)
        pg.draw.rect(screen, (80, 80, 80), bar_back)
        fill = pg.Rect(bar_back.x, bar_back.y, int(300 * self.hud.volume), 20)
        pg.draw.rect(screen, (0, 200, 100), fill)

        # 操作ガイド
        guide1 = FONT_SMALL.render("←/→ to change volume", True, (200, 200, 200))
        guide2 = FONT_SMALL.render("ESC or ENTER to return to pause menu", True, (200, 200, 200))
        screen.blit(guide1, (WIDTH // 2 - guide1.get_width() // 2, 400))
        screen.blit(guide2, (WIDTH // 2 - guide2.get_width() // 2, 430))

        # 戻るボタン
        back_rect = pg.Rect(WIDTH // 2 - 75, 480, 150, 50)
        pg.draw.rect(screen, (100, 100, 100), back_rect)
        pg.draw.rect(screen, (200, 200, 200), back_rect, 2)
        back_label = FONT_MED.render("Back", True, (255, 255, 255))
        screen.blit(back_label, (back_rect.centerx - back_label.get_width() // 2,
                                 back_rect.centery - back_label.get_height() // 2))

        self.back_rect = back_rect

    def handle_event(self, event):
        """
        設定画面のイベント処理。
        """
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_LEFT:
                self.hud.volume = max(0.0, self.hud.volume - 0.05)
                pg.mixer.music.set_volume(self.hud.volume)
            if event.key == pg.K_RIGHT:
                self.hud.volume = min(1.0, self.hud.volume + 0.05)
                pg.mixer.music.set_volume(self.hud.volume)
            if event.key == pg.K_ESCAPE or event.key == pg.K_RETURN:
                return "Back"
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # バーをクリックして音量変更
            bar = pg.Rect(WIDTH // 2 - 150, 320, 300, 20)
            if bar.collidepoint(mx, my):
                rel = (mx - bar.x) / bar.width
                self.hud.volume = min(1.0, max(0.0, rel))
                pg.mixer.music.set_volume(self.hud.volume)
            # 戻るボタン
            if self.back_rect.collidepoint(mx, my):
                return "Back"
        return None


# =====================
# タイトル画面
# =====================
def draw_title():
    screen.blit(TITLE_BG, (0, 0))

    overlay = pg.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(120)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # フォントパスがNoneの場合はデフォルトフォントを使用
    if FONT_PATH:
        font = pg.font.Font(FONT_PATH, 80)
        small = pg.font.Font(FONT_PATH, 36)
    else:
        font = pg.font.Font(None, 80)
        small = pg.font.Font(None, 36)

    title = font.render("こうかとん ファイター", True, (255, 255, 255))
    guide = small.render("ENTERキーでスタート", True, (230, 230, 230))

    screen.blit(title, (WIDTH//2 - title.get_width()//2, 220))
    screen.blit(guide, (WIDTH//2 - guide.get_width()//2, 330))


# =====================
# バトル選択画面
# =====================
def draw_select(selected):
    # 選択肢に応じた背景表示(ゲーム終了以外)
    if selected < len(STAGES):
        screen.blit(STAGES[selected]["bg"], (0, 0))
    else:
        screen.blit(STAGES[0]["bg"], (0, 0))

    overlay = pg.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(150)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    # フォントパスがNoneの場合はデフォルトフォントを使用
    if FONT_PATH:
        font = pg.font.Font(FONT_PATH, 60)
        small = pg.font.Font(FONT_PATH, 30)
    else:
        font = pg.font.Font(None, 60)
        small = pg.font.Font(None, 30)

    title = font.render("バトルステージ選択", True, (255, 255, 255))
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 60))

    # ステージ選択肢
    for i, stage in enumerate(STAGES):
        color = (255, 255, 0) if i == selected else (200, 200, 200)
        label = small.render(stage["name"], True, color)

        rect = pg.Rect(350, 180 + i * 80, 300, 50)
        pg.draw.rect(screen, color, rect, 2)
        screen.blit(
            label,
            (rect.centerx - label.get_width()//2,
             rect.centery - label.get_height()//2)
        )

    # ゲーム終了ボタン
    quit_index = len(STAGES)
    color = (255, 255, 0) if quit_index == selected else (200, 200, 200)
    label = small.render("ゲーム終了", True, color)
    rect = pg.Rect(350, 180 + quit_index * 80, 300, 50)
    pg.draw.rect(screen, color, rect, 2)
    screen.blit(
        label,
        (rect.centerx - label.get_width()//2,
         rect.centery - label.get_height()//2)
    )

    guide = small.render("↑↓で選択  ENTERで決定", True, (220, 220, 220))
    screen.blit(guide, (WIDTH//2 - guide.get_width()//2, 500))


# =====================
# メイン処理
# =====================
def main():
    game_state = TITLE
    selected_stage = 0
    current_stage = 0

    # グループ
    fighters = pg.sprite.Group()
    attacks = pg.sprite.Group()
    hurtboxes = pg.sprite.Group()

    p1 = Fighter(200, {
        "left": pg.K_a,
        "right": pg.K_d,
        "jump": pg.K_w,
        "punch": pg.K_c,
        "kick": pg.K_v
    }, "man")

    p2 = Fighter(700, {
        "left": pg.K_LEFT,
        "right": pg.K_RIGHT,
        "jump": pg.K_UP,
        "punch": pg.K_PERIOD,
        "kick": pg.K_SLASH
    }, "woman")

    fighters = [p1, p2]

    while True:
        screen.fill((30, 30, 30))
        key_lst = pg.key.get_pressed()
        
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN:
                for f in fighters:
                    if event.key == f.keys["punch"]:
                        f.do_attack("punch", attacks)
                    if event.key == f.keys["kick"]:
                        f.do_attack("kick", attacks)

        for f in fighters:
            f.update(key_lst)

        attacks.update()

        # HitBox × HurtBox
        for atk in attacks:
            for f in fighters:
                if f == atk.owner:
                    continue

                hit = False
                if atk.rect.colliderect(f.hurtbox):
                    hit = True
                elif f.attack_hurtbox and atk.rect.colliderect(f.attack_hurtbox):
                    hit = True

                if hit:
                    f.hp -= atk.damage
                    atk.kill()
                    break

        pg.draw.rect(screen, (80, 160, 80), (0, FLOOR, WIDTH, HEIGHT))

        for f in fighters:
            screen.blit(f.image, f.rect)
            pg.draw.rect(screen, (0, 0, 255), f.hurtbox, 1)
            if f.attack_hurtbox:
                pg.draw.rect(screen, (0, 200, 255), f.attack_hurtbox, 2)

        draw_hp(screen, p1, 50)
        draw_hp(screen, p2, WIDTH - 350)

        attacks.draw(screen)
        pg.display.update()

if __name__ == "__main__":
    main()
