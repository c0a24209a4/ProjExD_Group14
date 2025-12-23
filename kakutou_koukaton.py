import pygame as pg
import sys
import os

# =====================
# 初期設定
# =====================
WIDTH, HEIGHT = 1000, 600
FLOOR = HEIGHT - 50
os.chdir(os.path.dirname(os.path.abspath(__file__)))

pg.init()
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Mini Street Fighter")
clock = pg.time.Clock()

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
# 攻撃判定（HitBox）
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
# HPバー
# =====================
def draw_hp(screen, fighter, x):
    pg.draw.rect(screen, (255, 0, 0), (x, 20, 300, 20))
    pg.draw.rect(screen, (0, 255, 0), (x, 20, 3 * fighter.hp, 20))

# =====================
# メイン
# =====================
def main():
    attacks = pg.sprite.Group()

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
        clock.tick(60)

if __name__ == "__main__":
    main()
