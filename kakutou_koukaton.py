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
    def __init__(self, x, keys):
        super().__init__()

        # ===== 画像（サイズ手動調整）=====
        self.idle_r = pg.transform.scale(
            pg.image.load("fig/manfighter.png").convert_alpha(), (150, 200)  #画像の大きさ設定
        )
        self.idle_l = pg.transform.flip(self.idle_r, True, False)

        self.punch_r = pg.transform.scale(
            pg.image.load("fig/manfighter_punch.png").convert_alpha(), (150, 200)  #画像の大きさ設定
        )
        self.punch_l = pg.transform.flip(self.punch_r, True, False)

        self.kick_r = pg.transform.scale(
            pg.image.load("fig/manfighter_kick.png").convert_alpha(), (190, 200)  #画像の大きさ設定
        )
        self.kick_l = pg.transform.flip(self.kick_r, True, False)

        self.image = self.idle_r
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (x, FLOOR)

        self.vx = 0
        self.vy = 0
        self.on_ground = True

        self.hp = 100

        self.keys = keys
        self.facing = 1

        # ===== タイマー =====
        self.attack_timer = 0      # 技中
        self.recover_timer = 0     # 技後硬直（1秒）
        self.knockback_vx = 0      # ノックバック速度

    def update(self, key_lst):
        """
        入力に応じて移動・ジャンプ処理を行い、重力と地面判定を適用する。
        """
        self.vx = 0

        # ===== 行動可能判定 =====
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

        # ===== 技タイマー =====
        if self.attack_timer > 0:
            self.attack_timer -= 1
            if self.attack_timer == 0:
                self.recover_timer = 20  #  1/3秒硬直
        elif self.recover_timer > 0:
            self.recover_timer -= 1
        else:
            self.image = self.idle_r if self.facing == 1 else self.idle_l

        # ===== 重力 =====
        self.vy += 1
        self.rect.x += self.vx + self.knockback_vx
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



# =====================
# 攻撃クラス
# =====================
class Attack(pg.sprite.Sprite):
    DATA = {
        "punch": {"size": (40, 20), "life": 8, "damage": 5},
        "kick":  {"size": (60, 25), "life": 10, "damage": 8},
    }

    OFFSET_Y = {
        "punch": -10,
        "kick": 30
    }

    def __init__(self, fighter, atk_type):
        super().__init__()
        self.owner = fighter

        w, h = self.DATA[atk_type]["size"]
        self.image = pg.Surface((w, h), pg.SRCALPHA)
        self.image.fill((255, 0, 0, 150))

        self.rect = self.image.get_rect()

        # 発射時の位置をファイターの前方に設定
        if fighter.facing == 1:
            self.rect.left = fighter.rect.right + 10
        else:
            self.rect.right = fighter.rect.left - 10

        self.rect.centery = fighter.rect.centery + self.OFFSET_Y[atk_type]

        self.life = self.DATA[atk_type]["life"]
        self.damage = self.DATA[atk_type]["damage"]

    def update(self):
        """
        横移動し、寿命が尽きたら削除する。
        """
        # self.rect.x += self.vx
        self.life -= 1
        if self.life <= 0:
            self.kill()
            

# =====================
# ノックバック関数
# =====================
def apply_knockback(victim, attacker, damage):
    """
    ダメージを受けたファイターにノックバックを適用する
    
    Args:
        victim: ダメージを受けたファイター
        attacker: 攻撃したファイター
        damage: 与えたダメージ量
    """
    knockback_dir = 1 if attacker.facing == 1 else -1
    knockback_speed = knockback_dir * damage * 0.8
    victim.knockback_vx += knockback_speed
    victim.recover_timer = 15


# =====================
# くらい判定（HurtBox）
# =====================
class HurtBox(pg.sprite.Sprite):
    SIZE = {
        "punch": (60, 30),
        "kick":  (80, 40)
    }

    OFFSET_Y = {
        "punch": -10,
        "kick": 30
    }

    def __init__(self, fighter, atk_type):
        super().__init__()
        self.owner = fighter

        w, h = self.SIZE[atk_type]
        self.image = pg.Surface((w, h), pg.SRCALPHA)
        self.image.fill((0, 0, 255, 100))

        self.rect = self.image.get_rect()

        if fighter.facing == 1:
            self.rect.left = fighter.rect.right
        else:
            self.rect.right = fighter.rect.left

        self.rect.centery = fighter.rect.centery + self.OFFSET_Y[atk_type]

        self.life = 20  # 攻撃判定より長い

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

    def reset_timer(self):
        self.match_time = MATCH_TIME

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
    })

    p2 = Fighter(700, {
        "left": pg.K_LEFT,
        "right": pg.K_RIGHT,
        "jump": pg.K_UP,
        "punch": pg.K_PERIOD,
        "kick": pg.K_SLASH
    })

    fighters.add(p1, p2)

    # HUD とメニュー
    hud = HUD()
    pause_menu = PauseMenu(hud)
    settings_menu = SettingsMenu(hud)

    # 初期BGM(タイトル/メニュー)
    safe_load_and_play_bgm(MENU_BGM, hud.volume)

    running = True

    # 操作説明(下部)
    p1_keys_text = "P1: A/D Move  W Jump  C Punch  V Kick"
    p2_keys_text = "P2: ←/→ Move  ↑ Jump  . Punch  / Kick"

    # バトル画面の保存用(ポーズ時に背景として使う)
    battle_surface = None

    while running:
        dt_ms = clock.tick(60)
        dt = dt_ms / 1000.0
        screen.fill((30, 30, 30))
        key_lst = pg.key.get_pressed()
        
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()

            # ===== タイトル画面 =====
            if game_state == TITLE:
                if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                    game_state = SELECT

            # ===== ステージ選択画面 =====
            elif game_state == SELECT:
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_UP:
                        selected_stage = (selected_stage - 1) % (len(STAGES) + 1)
                    if event.key == pg.K_DOWN:
                        selected_stage = (selected_stage + 1) % (len(STAGES) + 1)
                    if event.key == pg.K_RETURN:
                        if selected_stage == len(STAGES):
                            running = False
                        else:
                            current_stage = selected_stage
                            game_state = BATTLE
                            hud.reset_timer()
                            p1.rect.bottomleft = (200, FLOOR)
                            p2.rect.bottomleft = (700, FLOOR)
                            p1.hp = 100
                            p2.hp = 100
                            attacks.empty()
                            hurtboxes.empty()
                            safe_load_and_play_bgm(BATTLE_BGM, hud.volume)

            # ===== バトル画面 =====
            elif game_state == BATTLE:
                if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                    game_state = PAUSED
                    battle_surface = screen.copy()

                if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                    if hud.pause_rect.collidepoint(event.pos):
                        game_state = PAUSED
                        battle_surface = screen.copy()

                if event.type == pg.KEYDOWN:
                    if event.key == p1.keys["punch"]:
                        p1.do_attack("punch", attacks, hurtboxes, p2)
                    if event.key == p1.keys["kick"]:
                        p1.do_attack("kick", attacks, hurtboxes, p2)
                    if event.key == p2.keys["punch"]:
                        p2.do_attack("punch", attacks, hurtboxes, p1)
                    if event.key == p2.keys["kick"]:
                        p2.do_attack("kick", attacks, hurtboxes, p1)

            # ===== ポーズ中 =====
            elif game_state == PAUSED:
                result = pause_menu.handle_event(event)
                if result == "Continue":
                    game_state = BATTLE
                elif result == "Settings":
                    game_state = SETTINGS
                elif result == "Quit":
                    game_state = SELECT
                    safe_load_and_play_bgm(MENU_BGM, hud.volume)

            # ===== 設定画面 =====
            elif game_state == SETTINGS:
                result = settings_menu.handle_event(event)
                if result == "Back":
                    game_state = PAUSED
        

        # ===== 描画・更新 =====
        if game_state == TITLE:
            draw_title()

        elif game_state == SELECT:
            draw_select(selected_stage)

        elif game_state == BATTLE:
            # 背景描画
            screen.blit(STAGES[current_stage]["bg"], (0, 0))

            # 時間の経過更新
            hud.update_time(dt)

            # 更新
            fighters.update(key_lst)
            attacks.update()
            hurtboxes.update()

            # ダメージ判定
            check_damage(attacks, hurtboxes)

            # 描画
            fighters.draw(screen)
            attacks.draw(screen)
            hurtboxes.draw(screen)
            
            # HPバー描画
            draw_hp(screen, p1, 50)
            draw_hp(screen, p2, WIDTH - 350)

            # HUD 描画
            hud.draw_top(screen)
            hud.draw_bottom_controls(screen, p1_keys_text, p2_keys_text)

            # 終了条件: HPが0か時間切れ
            if p1.hp <= 0 or p2.hp <= 0 or hud.match_time <= 0:
                # 勝者判定
                if p1.hp > p2.hp:
                    winner = "P1"
                    hud.p1_wins += 1
                elif p2.hp > p1.hp:
                    winner = "P2"
                    hud.p2_wins += 1
                else:
                    winner = "Draw"

                # 表示
                result_text = FONT_BIG.render("K.O." if (p1.hp <= 0 or p2.hp <= 0) else "Time Up", True, (255, 255, 0))
                screen.blit(result_text, (WIDTH // 2 - result_text.get_width() // 2, HEIGHT // 2 - 40))
                winner_text = FONT_MED.render(f"Winner: {winner}", True, (255, 255, 255))
                screen.blit(winner_text, (WIDTH // 2 - winner_text.get_width() // 2, HEIGHT // 2 + 30))
                pg.display.update()
                pg.time.delay(2000)

                # リセット
                p1.hp = 100
                p2.hp = 100
                attacks.empty()
                hud.reset_timer()
                safe_load_and_play_bgm(MENU_BGM, hud.volume)
                game_state = SELECT
                continue

        elif game_state == PAUSED:
            # バトル画面を背景として表示
            if battle_surface:
                screen.blit(battle_surface, (0, 0))
            pause_menu.draw(screen)

        elif game_state == SETTINGS:
            # バトル画面を背景として表示
            if battle_surface:
                screen.blit(battle_surface, (0, 0))
            settings_menu.draw(screen)

        pg.display.update()

if __name__ == "__main__":
    main()