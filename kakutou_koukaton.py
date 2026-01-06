import pygame as pg
import sys
import os
import platform

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
if platform.system() == "Windows":
    FONT_PATH = "C:/Windows/Fonts/msgothic.ttc"
elif platform.system() == "Darwin":  # macOS
    FONT_PATH = "/System/Library/Fonts/ヒラギノ角ゴシック W4.ttc"
else:  # Linux等
    FONT_PATH = None

# BGMファイル
MENU_BGM = "sound/bgm/menu-bgm.mp3"
BATTLE_BGM = "sound/bgm/vhs-tape.mp3"

# マッチ時間(秒)
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

def load_font(size):
    """フォントを安全にロードする関数"""
    if FONT_PATH and os.path.exists(FONT_PATH):
        try:
            return pg.font.Font(FONT_PATH, size)
        except:
            return pg.font.Font(None, size)
    else:
        return pg.font.Font(None, size)


# フォントの作成
FONT_BIG = load_font(80)
FONT_MED = load_font(36)
FONT_SMALL = load_font(13)

# フォントの作成
FONT_BIG = load_font(80)
FONT_MED = load_font(36)
FONT_SMALL = load_font(13)
# pg.init()
# screen = pg.display.set_mode((WIDTH, HEIGHT))
# pg.display.set_caption("Mini Street Fighter MAX")
# clock = pg.time.Clock()

def safe_load_and_play_bgm(path, volume=0.5, loops=-1):
    """BGMを安全にロードして再生する"""
    try:
        pg.mixer.music.load(path)
        pg.mixer.music.set_volume(volume)
        pg.mixer.music.play(loops)
    except Exception as e:
        print(f"[BGM load error] {path} : {e}")


# =====================
# 画像読み込み
# =====================
try:
    TITLE_BG = pg.transform.scale(
        pg.image.load("ダウンロード (1).jpg").convert(),
        (WIDTH, HEIGHT)
    )
except:
    TITLE_BG = pg.Surface((WIDTH, HEIGHT))
    TITLE_BG.fill((20, 20, 50))

# =====================
# ステージ定義
# =====================
STAGES = []
stage_files = [
    ("境内", "Tryfog.jpg"),
    ("稽古場", "ダウンロード.jpg"),
    ("繁華街(夜)", "3Dオリジナル背景作品 格闘ゲーム用背景.jpg")
]

for name, filename in stage_files:
    try:
        bg = pg.transform.scale(
            pg.image.load(filename).convert(),
            (WIDTH, HEIGHT)
        )
    except:
        bg = pg.Surface((WIDTH, HEIGHT))
        bg.fill((50, 50, 80))
    STAGES.append({"name": name, "bg": bg})


# =====================
# ノックバック関数
# =====================
def apply_knockback(target, attacker, damage):
    """ノックバックを適用"""
    knockback = damage * 2
    target.rect.x += knockback * attacker.facing
    if abs(knockback) > 10:
        target.vy = -8
        target.on_ground = False


# =====================
# HurtBoxクラス（追加）         いるかわからん
# =====================
class HurtBox(pg.sprite.Sprite):
    def __init__(self, fighter, atk_type):
        super().__init__()
        self.owner = fighter
        self.image = pg.Surface((1, 1), pg.SRCALPHA)  # 最小の透明サーフェス
        self.rect = self.image.get_rect()
        self.life = 20  # 短いライフタイム
        
    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.kill()

# =====================
# ノックバック関数
# =====================
def apply_knockback(target, attacker, damage):
    """ノックバックを適用"""
    knockback = damage * 2
    target.rect.x += knockback * attacker.facing
    if abs(knockback) > 10:
        target.vy = -8
        target.on_ground = False

# =====================
# Fighter クラス
# =====================
class Fighter(pg.sprite.Sprite):
    """
    プレイヤーキャラクターを表すクラス。
    移動・ジャンプ・攻撃・防御・しゃがみの状態を管理する。
    """

    def __init__(self, x: int, keys: dict[str, int], char_name: str) -> None:
        """
        Fighterを初期化する。

        Args:
            x: 初期X座標
            keys: 操作キー設定
            char_name: キャラクター名
        """
        super().__init__()
        self.energy = 100  # 追加：エネルギー
        self.throw_cool = 0  # 追加：投げクールダウン
        self.energy_regen = 0.1  # エネルギー回復速度

        # エネルギーと投げ技
        self.energy = 100
        self.throw_cool = 0
        self.energy_regen = 0.1

        # ===== 画像読み込み =====
        try:
            self.idle_r = pg.transform.scale(
                pg.image.load(f"fig/{char_name}fighter.png").convert_alpha(),
                (150, 200)
            )
        except:
            self.idle_r = pg.Surface((150, 200), pg.SRCALPHA)
            self.idle_r.fill((255, 100, 100, 255))
            
        self.idle_l = pg.transform.flip(self.idle_r, True, False)

        try:
            self.punch_r = pg.transform.scale(
                pg.image.load(f"fig/{char_name}fighter_punch.png").convert_alpha(),
                (150, 200)
            )
        except:
            self.punch_r = self.idle_r.copy()
            
        self.punch_l = pg.transform.flip(self.punch_r, True, False)

        try:
            self.kick_r = pg.transform.scale(
                pg.image.load(f"fig/{char_name}fighter_kick.png").convert_alpha(),
                (190, 200)
            )
        except:
            self.kick_r = pg.Surface((190, 200), pg.SRCALPHA)
            self.kick_r.fill((100, 255, 100, 255))
            
        self.kick_l = pg.transform.flip(self.kick_r, True, False)
        
        try:
            self.crouch_r = pg.transform.scale(
                pg.image.load(f"fig/{char_name}fighter_crouch.png").convert_alpha(),
                (110, 150)
            )
        except:
            self.crouch_r = pg.Surface((150, 140), pg.SRCALPHA)
            self.crouch_r.fill((100, 100, 255, 255))

        self.crouch_l = pg.transform.flip(self.crouch_r, True, False)

        self.image = self.idle_r
        self.rect = self.image.get_rect()
        self.rect.bottomleft = (x, FLOOR)

        # ===== HurtBox =====
        self.hurtbox = pg.Rect(0, 0, 60, 180)
        self.update_hurtbox()
        self.attack_hurtbox = None

        # 物理パラメータ
        self.vx: int = 0
        self.vy: int = 0
        self.walk_speed: int = 6
        self.on_ground: bool = True

        # ステータス
        self.hp: int = 100
        self.facing: int = 1

        # 入力設定
        self.keys = keys

        # 状態管理
        self.is_guarding: bool = False
        self.is_crouching: bool = False
        self.is_attacking: bool = False
        self.attack_timer: int = 0
        self.recover_timer: int = 0

    def update_hurtbox(self):
        """本体のくらい判定を更新"""
        self.hurtbox.centerx = self.rect.centerx
        self.hurtbox.bottom = self.rect.bottom

    def update_attack_hurtbox(self):
        """攻撃中のくらい判定を更新"""
        if self.attack_timer == 0:
            self.attack_hurtbox = None
            return

        if self.image in (self.punch_r, self.punch_l):
            w, h = 65, 30
            offset_x = 70 if self.facing == 1 else -70
            offset_y = 60
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

    def update(self, key_lst: list[bool], enemy: "Fighter" = None) -> None:
        """
        キャラクターの状態更新を行う。

        Args:
            key_lst: pygame.key.get_pressed() の結果
            enemy: 対戦相手の Fighter
        """
        self.vx = 0
        self.is_guarding = False

        # 攻撃・硬直中フレーム管理
        if self.attack_timer > 0:
            self.attack_timer -= 1
            if self.attack_timer == 0:
                self.recover_timer = 10
        elif self.recover_timer > 0:
            self.recover_timer -= 1
        else:
            self.is_attacking = False

        # 投げクールダウン更新
        if self.throw_cool > 0:
            self.throw_cool -= 1

        # エネルギー回復
        if self.energy < 100:
            self.energy += self.energy_regen

        can_move = (self.attack_timer == 0 and self.recover_timer == 0)

        # =====================
        # しゃがみ処理
        # =====================
        if key_lst[self.keys["down"]] and self.on_ground and can_move:
            if not self.is_crouching:
                self.is_crouching = True
                old_bottom = self.rect.bottom
                self.image = self.crouch_r if self.facing == 1 else self.crouch_l
                self.rect = self.image.get_rect(
                    midbottom=(self.rect.centerx, old_bottom)
                )
        else:
            if self.is_crouching:
                self.is_crouching = False
                self.image = self.idle_r if self.facing == 1 else self.idle_l
                self.rect = self.image.get_rect(midbottom=self.rect.midbottom)

        # =====================
        # 防御処理（攻撃中・しゃがみ中は不可）
        # =====================
        if not self.is_attacking and not self.is_crouching and enemy and can_move:
            back_key = (
                self.keys["left"]
                if enemy.rect.centerx > self.rect.centerx
                else self.keys["right"]
            )

            if key_lst[back_key]:
                self.is_guarding = True
                self.vx = (
                    -1 if back_key == self.keys["left"] else 1
                ) * (self.walk_speed // 2)

        # =====================
        # 通常移動
        # =====================
        if not self.is_guarding and not self.is_crouching and can_move:
            if key_lst[self.keys["left"]]:
                self.vx = -self.walk_speed
                self.facing = -1
            if key_lst[self.keys["right"]]:
                self.vx = self.walk_speed
                self.facing = 1

        # =====================
        # ジャンプ
        # =====================
        if (key_lst[self.keys["jump"]] and self.on_ground and 
            not self.is_crouching and can_move):
            self.vy = -20
            self.on_ground = False

        # 待機画像更新
        if (self.attack_timer == 0 and self.recover_timer == 0 and 
            not self.is_crouching):
            self.image = self.idle_r if self.facing == 1 else self.idle_l

        # =====================
        # 重力・位置更新
        # =====================
        self.vy += 1
        self.rect.x += self.vx
        self.rect.y += self.vy

        if self.rect.bottom >= FLOOR:
            self.rect.bottom = FLOOR
            self.vy = 0
            self.on_ground = True

        self.update_hurtbox()
        self.update_attack_hurtbox()

    def do_attack(self, atk_type, attacks):
        """攻撃を実行"""
        if self.attack_timer > 0 or self.recover_timer > 0:
            return

        if atk_type == "punch":
            self.image = self.punch_r if self.facing == 1 else self.punch_l
            self.attack_timer = 10
            self.is_attacking = True
        elif atk_type == "kick":
            self.image = self.kick_r if self.facing == 1 else self.kick_l
            self.attack_timer = 15
            self.is_attacking = True

        attacks.add(Attack(self, atk_type))


# =====================
# 攻撃クラス
# =====================
class Attack(pg.sprite.Sprite):
    """攻撃判定用のヒットボックスクラス"""

    DATA = {
        "punch": {"size": (40, 20), "life": 6, "damage": 5},
        "kick": {"size": (65, 25), "life": 8, "damage": 8},
    }

    def __init__(self, fighter: Fighter, atk_type: str) -> None:
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

    def update(self) -> None:
        """攻撃判定の寿命管理"""
        self.life -= 1
        if self.life <= 0:
            self.kill()


# =====================
# 飛び道具
# =====================
class Projectile(pg.sprite.Sprite):
    def __init__(self, fighter, kind):
        super().__init__()
        self.owner = fighter
        self.kind = kind
        self.facing = fighter.facing
        self.angle = 0
        self.rotate_speed = 0

        if kind == "beam":
            try:
                self.original_image = pg.transform.scale(
                    pg.image.load("fig/syuriken.png").convert_alpha(), (30, 30)
                )
            except:
                self.original_image = pg.Surface((30, 30), pg.SRCALPHA)
                self.original_image.fill((255, 200, 0, 255))

            self.hitbox_size = (15, 15)
            self.speed = 12
            self.damage = 10
            self.rotate_speed = 20

        elif kind == "bomb":
            try:
                self.original_image = pg.transform.scale(
                    pg.image.load("fig/rasengan1.png").convert_alpha(), (80, 80)
                )
            except:
                self.original_image = pg.Surface((80, 80), pg.SRCALPHA)
                self.original_image.fill((0, 150, 255, 255))

            self.hitbox_size = (40, 40)
            self.speed = 8
            self.damage = 15
            self.rotate_speed = 0

        elif kind == "rasensyuriken":
            try:
                self.original_image = pg.transform.scale(
                    pg.image.load("fig/rasensyuriken.png").convert_alpha(), (80, 80)
                )
            except:
                self.original_image = pg.Surface((80, 80), pg.SRCALPHA)
                self.original_image.fill((255, 100, 0, 255))

            self.hitbox_size = (45, 45)
            self.speed = 8
            self.damage = 30
            self.rotate_speed = 15

        if self.facing == -1:
            self.original_image = pg.transform.flip(self.original_image, True, False)

        self.image = self.original_image.copy()
        self.rect = self.original_image.get_rect()
        self.hitbox = pg.Rect(0, 0, *self.hitbox_size)

        if self.facing == 1:
            self.rect.midleft = fighter.rect.midright
        else:
            self.rect.midright = fighter.rect.midleft

        self.hitbox.center = self.rect.center

    def update(self):
        self.rect.x += self.speed * self.facing
        self.hitbox.center = self.rect.center

        if self.rotate_speed != 0:
            self.angle = (self.angle + self.rotate_speed) % 360
            center = self.rect.center
            self.image = pg.transform.rotate(self.original_image, self.angle)
            self.rect = self.image.get_rect(center=center)
            self.hitbox.center = center

        if self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()


# =====================
# 投げ技
# =====================
def try_throw(attacker, defender):
    """投げ技を試行"""
    if attacker.throw_cool > 0:
        return False

    dist = abs(attacker.rect.centerx - defender.rect.centerx)
    height = abs(attacker.rect.bottom - defender.rect.bottom)

    if dist < 70 and height < 20:
        defender.hp -= 20
        knock = 140
        defender.rect.x += knock * attacker.facing
        defender.vy = -15
        defender.on_ground = False
        attacker.energy = min(100, attacker.energy + 10)
        attacker.throw_cool = 40
        return True
    return False


# =====================
# HPバー
# =====================
def draw_hp(screen, fighter, x):
    pg.draw.rect(screen, (255, 0, 0), (x, 20, 300, 20))
    pg.draw.rect(screen, (0, 255, 0), (x, 20, 3 * fighter.hp, 20))

            
# =====================
# HUD クラス
# =====================
class HUD:
    """画面上部のタイマー・スコア・ポーズボタン・下部の操作説明を描画"""

    def __init__(self):
        self.match_time = MATCH_TIME
        self.p1_wins = 0
        self.p2_wins = 0
        self.pause_rect = pg.Rect(WIDTH - 110, 70, 100, 40)
        self.volume = 0.5
        self.last_time_check = pg.time.get_ticks()

    def update_time(self):
        """秒単位の時間を減少させる"""
        current_time = pg.time.get_ticks()
        elapsed = (current_time - self.last_time_check) / 1000.0
        if elapsed >= 1.0:
            self.match_time = max(0, self.match_time - 1)
            self.last_time_check = current_time

    def draw_top(self, screen):
        """上部中央に時間、左/右にスコア、右上にポーズボタンを描画"""
        score_left = FONT_MED.render(f"P1 Wins: {self.p1_wins}", True, (255, 255, 255))
        score_right = FONT_MED.render(f"P2 Wins: {self.p2_wins}", True, (255, 255, 255))
        screen.blit(score_left, (10, 10))
        screen.blit(score_right, (WIDTH - 10 - score_right.get_width(), 10))

        time_sec = int(self.match_time)
        if time_sec <= 30 and time_sec % 2 == 0:
            time_color = (255, 0, 0)
        else:
            time_color = (255, 255, 255)

        time_text = FONT_MED.render(f"Time: {time_sec}", True, time_color)
        screen.blit(time_text, (WIDTH // 2 - time_text.get_width() // 2, 10))

        pg.draw.rect(screen, (180, 180, 180), self.pause_rect)
        p_label = FONT_SMALL.render("PAUSE", True, (0, 0, 0))
        screen.blit(p_label, (self.pause_rect.centerx - p_label.get_width() // 2,
                              self.pause_rect.centery - p_label.get_height() // 2))

    def draw_bottom_controls(self, screen, p1_keys_text, p2_keys_text):
        """画面下部に操作説明を表示"""
        rect = pg.Rect(0, HEIGHT - 40, WIDTH, 40)
        pg.draw.rect(screen, (40, 40, 40), rect)
        left = FONT_SMALL.render(p1_keys_text, True, (220, 220, 220))
        right = FONT_SMALL.render(p2_keys_text, True, (220, 220, 220))
        screen.blit(left, (10, HEIGHT - 32))
        screen.blit(right, (WIDTH - 10 - right.get_width(), HEIGHT - 32))


# =====================
# ポーズメニュー
# =====================
class PauseMenu:
    """ポーズ画面。続行・設定・終了メニュー"""

    def __init__(self, hud):
        self.options = ["Continue", "Settings", "Quit"]
        self.selected = 0
        self.hud = hud

    def draw(self, screen):
        overlay = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        title = FONT_BIG.render("Paused", True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        for i, opt in enumerate(self.options):
            color = (255, 255, 0) if i == self.selected else (220, 220, 220)
            label = FONT_MED.render(opt, True, color)
            rect = label.get_rect(center=(WIDTH // 2, 220 + i * 70))
            screen.blit(label, rect)

        guide = FONT_SMALL.render("↑↓ Select  ENTER Confirm  SPACE Continue", True, (200, 200, 200))
        screen.blit(guide, (WIDTH // 2 - guide.get_width() // 2, 500))

    def handle_event(self, event):
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
            mx, my = event.pos
            for i, opt in enumerate(self.options):
                label = FONT_MED.render(opt, True, (0, 0, 0))
                rect = label.get_rect(center=(WIDTH // 2, 220 + i * 70))
                if rect.collidepoint(mx, my):
                    return opt
        return None


# =====================
# 設定メニュー
# =====================
class SettingsMenu:
    """設定画面(音量調整)"""

    def __init__(self, hud):
        self.hud = hud

    def draw(self, screen):
        overlay = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        title = FONT_BIG.render("Settings", True, (255, 255, 255))
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 100))

        vol_text = FONT_MED.render(f"Music Volume: {int(self.hud.volume * 100)}%", True, (255, 255, 255))
        screen.blit(vol_text, (WIDTH // 2 - vol_text.get_width() // 2, 250))

        bar_back = pg.Rect(WIDTH // 2 - 150, 320, 300, 20)
        pg.draw.rect(screen, (80, 80, 80), bar_back)
        fill = pg.Rect(bar_back.x, bar_back.y, int(300 * self.hud.volume), 20)
        pg.draw.rect(screen, (0, 200, 100), fill)

        guide1 = FONT_SMALL.render("←/→ to change volume", True, (200, 200, 200))
        guide2 = FONT_SMALL.render("ESC or ENTER to return to pause menu", True, (200, 200, 200))
        screen.blit(guide1, (WIDTH // 2 - guide1.get_width() // 2, 400))
        screen.blit(guide2, (WIDTH // 2 - guide2.get_width() // 2, 430))

        back_rect = pg.Rect(WIDTH // 2 - 75, 480, 150, 50)
        pg.draw.rect(screen, (100, 100, 100), back_rect)
        pg.draw.rect(screen, (200, 200, 200), back_rect, 2)
        back_label = FONT_MED.render("Back", True, (255, 255, 255))
        screen.blit(back_label, (back_rect.centerx - back_label.get_width() // 2,
                                 back_rect.centery - back_label.get_height() // 2))

        self.back_rect = back_rect

    def handle_event(self, event):
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
            bar = pg.Rect(WIDTH // 2 - 150, 320, 300, 20)
            if bar.collidepoint(mx, my):
                rel = (mx - bar.x) / bar.width
                self.hud.volume = min(1.0, max(0.0, rel))
                pg.mixer.music.set_volume(self.hud.volume)
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

    title = FONT_BIG.render("こうかとん ファイター", True, (255, 255, 255))
    guide = FONT_MED.render("ENTERキーでスタート", True, (230, 230, 230))

    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 220))
    screen.blit(guide, (WIDTH // 2 - guide.get_width() // 2, 330))


# =====================
# バトル選択画面
# =====================
def draw_select(selected):
    if selected < len(STAGES):
        screen.blit(STAGES[selected]["bg"], (0, 0))
    else:
        screen.blit(STAGES[0]["bg"], (0, 0))

    overlay = pg.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(150)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    title = FONT_BIG.render("バトルステージ選択", True, (255, 255, 255))
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))

    for i, stage in enumerate(STAGES):
        color = (255, 255, 0) if i == selected else (200, 200, 200)
        label = FONT_MED.render(stage["name"], True, color)
        rect = pg.Rect(350, 180 + i * 80, 300, 50)
        pg.draw.rect(screen, color, rect, 2)
        screen.blit(label, (rect.centerx - label.get_width() // 2,
                            rect.centery - label.get_height() // 2))

    quit_index = len(STAGES)
    color = (255, 255, 0) if quit_index == selected else (200, 200, 200)
    label = FONT_MED.render("ゲーム終了", True, color)
    rect = pg.Rect(350, 180 + quit_index * 80, 300, 50)
    pg.draw.rect(screen, color, rect, 2)
    screen.blit(label, (rect.centerx - label.get_width() // 2,
                        rect.centery - label.get_height() // 2))

    guide = FONT_MED.render("↑↓で選択  ENTERで決定", True, (220, 220, 220))
    screen.blit(guide, (WIDTH // 2 - guide.get_width() // 2, 500))


# =====================
# メイン処理
# =====================
def main() -> None:
    """ゲームのメインループ"""
    game_state = TITLE
    selected_stage = 0
    current_stage = 0

    # スプライトグループ
    attacks = pg.sprite.Group()
    projectiles = pg.sprite.Group()

    # プレイヤー作成
    p1 = Fighter(200, {
        "left": pg.K_a,
        "right": pg.K_d,
        "jump": pg.K_w,
        "down": pg.K_s,
        "punch": pg.K_c,
        "kick": pg.K_v,
        "beam": pg.K_g,
        "bomb": pg.K_h,
        "throw": pg.K_t,
    }, "man")

    p2 = Fighter(700, {
        "left": pg.K_LEFT,
        "right": pg.K_RIGHT,
        "jump": pg.K_UP,
        "down": pg.K_DOWN,
        "punch": pg.K_PERIOD,
        "kick": pg.K_SLASH,
        "beam": pg.K_COLON,
        "bomb": pg.K_SEMICOLON,
        "throw": pg.K_RIGHTBRACKET,
    }, "woman")

    fighters = [p1, p2]

    # HUD とメニュー
    hud = HUD()
    pause_menu = PauseMenu(hud)
    settings_menu = SettingsMenu(hud)

    # 初期BGM
    safe_load_and_play_bgm(MENU_BGM, hud.volume)

    running = True

    # 操作説明
    p1_keys_text = "P1: A/D=移動 W=ジャンプ S=しゃがみ C=パンチ V=キック G=手裏剣 H=螺旋丸 T=投げ"
    p2_keys_text = "P2: ←/→=移動 ↑=ジャンプ ↓=しゃがみ .=パンチ /=キック :=手裏剣 ;=螺旋丸 ]=投げ"

    battle_surface = None

    while running:
        dt_ms = clock.tick(60)
        dt = dt_ms / 1000.0

        key_lst = pg.key.get_pressed()

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

            # ===== タイトル =====
            if game_state == TITLE:
                if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                    game_state = SELECT

            # ===== バトル選択 =====
            elif game_state == SELECT:
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_UP:
                        selected_stage = (selected_stage - 1) % (len(STAGES) + 1)
                    elif event.key == pg.K_DOWN:
                        selected_stage = (selected_stage + 1) % (len(STAGES) + 1)
                    elif event.key == pg.K_RETURN:
                        if selected_stage < len(STAGES):
                            game_state = BATTLE
                            current_stage = selected_stage
                            hud.match_time = MATCH_TIME
                            hud.last_time_check = pg.time.get_ticks()
                            p1.hp = 100
                            p2.hp = 100
                            p1.energy = 100
                            p2.energy = 100
                            p1.rect.bottomleft = (200, FLOOR)
                            p2.rect.bottomleft = (700, FLOOR)
                            p1.facing = 1
                            p2.facing = -1
                            attacks.empty()
                            projectiles.empty()
                            safe_load_and_play_bgm(BATTLE_BGM, hud.volume)
                        else:
                            running = False

            # ===== バトル中の入力 =====
            elif game_state == BATTLE:
                if event.type == pg.KEYDOWN:
                    # パンチ・キック
                    for f in fighters:
                        if event.key == f.keys["punch"]:
                            f.do_attack("punch", attacks)
                        if event.key == f.keys["kick"]:
                            f.do_attack("kick", attacks)

                    # 飛び道具
                    if event.key == p1.keys["beam"] and p1.energy >= 20:
                        projectiles.add(Projectile(p1, "beam"))
                        p1.energy -= 20
                    if event.key == p1.keys["bomb"] and p1.energy >= 30:
                        projectiles.add(Projectile(p1, "bomb"))
                        p1.energy -= 30

                    if event.key == p2.keys["beam"] and p2.energy >= 20:
                        projectiles.add(Projectile(p2, "beam"))
                        p2.energy -= 20
                    if event.key == p2.keys["bomb"] and p2.energy >= 30:
                        projectiles.add(Projectile(p2, "bomb"))
                        p2.energy -= 30

                    # 投げ技
                    if event.key == p1.keys["throw"]:
                        try_throw(p1, p2)
                    if event.key == p2.keys["throw"]:
                        try_throw(p2, p1)

                    # ESCキーでポーズ
                    if event.key == pg.K_ESCAPE:
                        game_state = PAUSED
                        battle_surface = screen.copy()

                # ポーズボタンクリック
                elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if hud.pause_rect.collidepoint(mx, my):
                        game_state = PAUSED
                        battle_surface = screen.copy()

            # ===== ポーズ中の入力 =====
            elif game_state == PAUSED:
                result = pause_menu.handle_event(event)
                if result == "Continue":
                    game_state = BATTLE
                elif result == "Settings":
                    game_state = SETTINGS
                elif result == "Quit":
                    game_state = SELECT
                    safe_load_and_play_bgm(MENU_BGM, hud.volume)

            # ===== 設定画面の入力 =====
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
            # ステージ背景描画
            screen.blit(STAGES[current_stage]["bg"], (0, 0))

            # 床描画
            pg.draw.rect(screen, (80, 160, 80), (0, FLOOR, WIDTH, HEIGHT))

            # 時間更新
            hud.update_time()

            # ファイター更新
            p1.update(key_lst, p2)
            p2.update(key_lst, p1)

            attacks.update()
            projectiles.update()

            # 飛び道具融合判定
            proj_list = list(projectiles)
            for i in range(len(proj_list)):
                for j in range(i + 1, len(proj_list)):
                    p1_proj = proj_list[i]
                    p2_proj = proj_list[j]

                    if (p1_proj.owner == p2_proj.owner and
                        {p1_proj.kind, p2_proj.kind} == {"beam", "bomb"} and
                        pg.sprite.collide_rect(p1_proj, p2_proj)):

                        x = (p1_proj.rect.centerx + p2_proj.rect.centerx) // 2
                        y = (p1_proj.rect.centery + p2_proj.rect.centery) // 2

                        p1_proj.kill()
                        p2_proj.kill()

                        new_proj = Projectile(p1_proj.owner, "rasensyuriken")
                        new_proj.rect.center = (x, y)
                        new_proj.hitbox.center = (x, y)
                        projectiles.add(new_proj)
                        break

            # 攻撃判定
            for atk in attacks:
                for f in fighters:
                    if f == atk.owner:
                        continue

                    hit = False
                    damage = atk.damage

                    # 防御中は軽減
                    if f.is_guarding:
                        damage = damage // 3

                    if atk.rect.colliderect(f.hurtbox):
                        hit = True
                    elif f.attack_hurtbox and atk.rect.colliderect(f.attack_hurtbox):
                        hit = True

                    if hit:
                        f.hp -= damage
                        apply_knockback(f, atk.owner, damage)
                        atk.kill()
                        break

            # 飛び道具とファイターの衝突判定
            for proj in projectiles:
                for f in fighters:
                    if f != proj.owner and proj.hitbox.colliderect(f.hurtbox):
                        damage = proj.damage
                        if f.is_guarding:
                            damage = damage // 3
                        f.hp -= damage
                        apply_knockback(f, proj.owner, damage)
                        proj.kill()
                        break

            # HPバーの描画
            draw_hp(screen, p1, 50)
            draw_hp(screen, p2, WIDTH - 350)
            
            # エネルギーバーの描画
            pg.draw.rect(screen, (100, 100, 100), (50, 45, 300, 12))
            energy_width1 = 3 * max(0, p1.energy)
            pg.draw.rect(screen, (0, 150, 255), (50, 45, energy_width1, 12))
            pg.draw.rect(screen, (255, 255, 255), (50, 45, 300, 12), 1)
            
            pg.draw.rect(screen, (100, 100, 100), (WIDTH - 350, 45, 300, 12))
            energy_width2 = 3 * max(0, p2.energy)
            pg.draw.rect(screen, (0, 150, 255), (WIDTH - 350, 45, energy_width2, 12))
            pg.draw.rect(screen, (255, 255, 255), (WIDTH - 350, 45, 300, 12), 1)

            # エネルギーバーの描画
            pg.draw.rect(screen, (100, 100, 100), (50, 45, 300, 12))
            energy_width1 = 3 * max(0, p1.energy)
            pg.draw.rect(screen, (0, 150, 255), (50, 45, energy_width1, 12))
            pg.draw.rect(screen, (255, 255, 255), (50, 45, 300, 12), 1)

            pg.draw.rect(screen, (100, 100, 100), (WIDTH - 350, 45, 300, 12))
            energy_width2 = 3 * max(0, p2.energy)
            pg.draw.rect(screen, (0, 150, 255), (WIDTH - 350, 45, energy_width2, 12))
            pg.draw.rect(screen, (255, 255, 255), (WIDTH - 350, 45, 300, 12), 1)

            # ファイター描画
            for f in fighters:
                screen.blit(f.image, f.rect)

            # 攻撃描画
            attacks.draw(screen)

            # 飛び道具描画
            for proj in projectiles:
                screen.blit(proj.image, proj.rect)

            # HUD描画
            hud.draw_top(screen)
            hud.draw_bottom_controls(screen, p1_keys_text, p2_keys_text)

            # 勝利判定
            if hud.match_time <= 0 or p1.hp <= 0 or p2.hp <= 0:
                if p1.hp > p2.hp:
                    hud.p1_wins += 1
                elif p2.hp > p1.hp:
                    hud.p2_wins += 1

                result_text = (FONT_BIG.render("K.O.", True, (255, 255, 0))
                               if (p1.hp <= 0 or p2.hp <= 0)
                               else FONT_BIG.render("Time Up", True, (255, 255, 0)))
                screen.blit(result_text, (WIDTH // 2 - result_text.get_width() // 2, HEIGHT // 2 - 40))
                pg.display.update()
                pg.time.delay(2000)

                attacks.empty()
                projectiles.empty()

                game_state = SELECT
                safe_load_and_play_bgm(MENU_BGM, hud.volume)

        elif game_state == PAUSED:
            if battle_surface:
                screen.blit(battle_surface, (0, 0))
            pause_menu.draw(screen)

        elif game_state == SETTINGS:
            if battle_surface:
                screen.blit(battle_surface, (0, 0))
            settings_menu.draw(screen)

        pg.display.update()

    pg.quit()
    sys.exit()

if __name__ == "__main__":
    main()
    pg.quit()
    sys.exit()