from __future__ import division
from os import path
import pygame, random

imgDir = path.join(path.dirname(__file__), 'assets')
soundDir = path.join(path.dirname(__file__), 'sounds')

WIDTH, HEIGHT = 480, 600
FPS, POWERUP_TIME = 60, 5000
BAR_LENGTH, BAR_HEIGHT = 100, 10

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)


pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Shooter")
clock = pygame.time.Clock()


fontName = pygame.font.match_font('arial')


def main():
    global SCREEN


def drawText(surf, text, size, x, y):
    font = pygame.font.Font(fontName, size)
    textSurf = font.render(text, True, WHITE)
    textRect = textSurf.get_rect()
    textRect.midtop = (x, y)
    surf.blit(textSurf, textRect)


def drawShieldBar(surf, x, y, pct):
    pct = max(pct, 0)
    fill = (pct / 100) * BAR_LENGTH
    outlineRect = pygame.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
    fillRect = pygame.Rect(x, y, fill, BAR_HEIGHT)
    pygame.draw.rect(surf, GREEN, fillRect)
    pygame.draw.rect(surf, WHITE, outlineRect, 2)


def drawLives(surf, x, y, lives, img):
    for i in range(lives):
        imgRect = img.get_rect()
        imgRect.x = x + 30 * i
        imgRect.y = y
        surf.blit(img, imgRect)


def newMob():
    mobElement = Mob()
    allSprites.add(mobElement)
    mobs.add(mobElement)


class Explosion(pygame.sprite.Sprite):
    def __init__(self, center, size):
        pygame.sprite.Sprite.__init__(self)
        self.size = size
        self.image = explosionAnim[self.size][0]
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.frame = 0
        self.lastUpdate = pygame.time.get_ticks()
        self.frameRate = 75

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.lastUpdate > self.frameRate:
            self.lastUpdate = now
            self.frame += 1
            if self.frame == len(explosionAnim[self.size]):
                self.kill()
            else:
                center = self.rect.center
                self.image = explosionAnim[self.size][self.frame]
                self.rect = self.image.get_rect()
                self.rect.center = center


class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.transform.scale(playerImg, (50, 38))
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.radius = 20
        self.rect.centerx = WIDTH / 2
        self.rect.bottom = HEIGHT - 10
        self.speedx = 0
        self.shield = 100
        self.shootDelay = 250
        self.lastShot = pygame.time.get_ticks()
        self.lives = 3
        self.hidden = False
        self.hideTimer = pygame.time.get_ticks()
        self.power = 1
        self.powerTimer = pygame.time.get_ticks()

    def update(self):
        if self.power >= 2 and pygame.time.get_ticks() - self.powerTime > POWERUP_TIME:
            self.power -= 1
            self.powerTime = pygame.time.get_ticks()

        if self.hidden and pygame.time.get_ticks() - self.hideTimer > 1000:
            self.hidden = False
            self.rect.centerx = WIDTH / 2
            self.rect.bottom = HEIGHT - 30

        self.speedx = 0

        keystate = pygame.key.get_pressed()
        if keystate[pygame.K_LEFT]:
            self.speedx = -5
        elif keystate[pygame.K_RIGHT]:
            self.speedx = 5

        if keystate[pygame.K_SPACE]:
            self.shoot()

        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
        if self.rect.left < 0:
            self.rect.left = 0

        self.rect.x += self.speedx

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.lastShot > self.shootDelay:
            self.lastShot = now
            if self.power == 1:
                bullet = Bullet(self.rect.centerx, self.rect.top)
                allSprites.add(bullet)
                bullets.add(bullet)
                shootingSound.play()
            if self.power == 2:
                bullet1 = Bullet(self.rect.left, self.rect.centery)
                bullet2 = Bullet(self.rect.right, self.rect.centery)
                allSprites.add(bullet1)
                allSprites.add(bullet2)
                bullets.add(bullet1)
                bullets.add(bullet2)
                shootingSound.play()

            if self.power >= 3:
                bullet1 = Bullet(self.rect.left, self.rect.centery)
                bullet2 = Bullet(self.rect.right, self.rect.centery)
                missile1 = Missile(self.rect.centerx, self.rect.top)

                allSprites.add(bullet1)
                allSprites.add(bullet2)
                allSprites.add(missile1)
                bullets.add(bullet1)
                bullets.add(bullet2)
                bullets.add(missile1)
                shootingSound.play()
                missileSound.play()

    def powerup(self):
        self.power += 1
        self.powerTime = pygame.time.get_ticks()

    def hide(self):
        self.hidden = True
        self.hideTimer = pygame.time.get_ticks()
        self.rect.center = (WIDTH / 2, HEIGHT + 200)


class Mob(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.imageOrig = random.choice(meteorImages)
        self.imageOrig.set_colorkey(BLACK)
        self.image = self.imageOrig.copy()
        self.rect = self.image.get_rect()
        self.radius = int(self.rect.width * .90 / 2)
        self.rect.x = random.randrange(0, WIDTH - self.rect.width)
        self.rect.y = random.randrange(-150, -100)
        self.speedy = random.randrange(5, 20)
        self.speedx = random.randrange(-3, 3)
        self.rotation = 0
        self.rotationSpeed = random.randrange(-8, 8)
        self.lastUpdate = pygame.time.get_ticks()

    def rotate(self):
        timeNow = pygame.time.get_ticks()
        if timeNow - self.lastUpdate > 50:
            self.lastUpdate = timeNow
            self.rotation = (self.rotation + self.rotationSpeed) % 360
            newImage = pygame.transform.rotate(self.imageOrig, self.rotation)
            oldCenter = self.rect.center
            self.image = newImage
            self.rect = self.image.get_rect()
            self.rect.center = oldCenter

    def update(self):
        self.rotate()
        self.rect.x += self.speedx
        self.rect.y += self.speedy

        if (self.rect.top > HEIGHT + 10) or (self.rect.left < -25) or (self.rect.right >  WIDTH + 20):
            self.rect.x = random.randrange(0, WIDTH - self.rect.width)
            self.rect.y = random.randrange(-100, -40)
            self.speedy = random.randrange(1, 8)


class Pow(pygame.sprite.Sprite):
    def __init__(self, center):
        pygame.sprite.Sprite.__init__(self)
        self.type = random.choice(['shield', 'gun'])
        self.image = powerUpImages[self.type]
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()

        self.rect.center = center
        self.speedy = 2

    def update(self):
        self.rect.y += self.speedy
        if self.rect.top > HEIGHT:
            self.kill()


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = bulletImg
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()

        self.rect.bottom = y
        self.rect.centerx = x
        self.speedy = -10

    def update(self):
        self.rect.y += self.speedy
        if self.rect.bottom < 0:
            self.kill()


class Missile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = missileImg
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()
        self.rect.bottom = y
        self.rect.centerx = x
        self.speedy = -10

    def update(self):
        self.rect.y += self.speedy
        if self.rect.bottom < 0:
            self.kill()


background = pygame.image.load(path.join(imgDir, 'starfield.png')).convert()
backgroundRect = background.get_rect()

playerImg = pygame.image.load(path.join(imgDir, 'playerShip1_orange.png')).convert()
playerMiniImg = pygame.transform.scale(playerImg, (25, 19))
playerMiniImg.set_colorkey(BLACK)
bulletImg = pygame.image.load(path.join(imgDir, 'laserRed16.png')).convert()
missileImg = pygame.image.load(path.join(imgDir, 'missile.png')).convert_alpha()

meteorImages = []
meteorList = [
    'meteorBrown_big1.png',
    'meteorBrown_big2.png',
    'meteorBrown_med1.png',
    'meteorBrown_med3.png',
    'meteorBrown_small1.png',
    'meteorBrown_small2.png',
    'meteorBrown_tiny1.png',
]

for image in meteorList:
    meteorImages.append(pygame.image.load(path.join(imgDir, image)).convert())

explosionAnim = {'lg': [], 'sm': [], 'player': []}
for i in range(9):
    filename = f'regularExplosion0{i}.png'
    img = pygame.image.load(path.join(imgDir, filename)).convert()
    img.set_colorkey(BLACK)

    imgLg = pygame.transform.scale(img, (75, 75))
    explosionAnim['lg'].append(imgLg)
    imgSm = pygame.transform.scale(img, (32, 32))
    explosionAnim['sm'].append(imgSm)

    filename = f'sonicExplosion0{i}.png'
    img = pygame.image.load(path.join(imgDir, filename)).convert()
    img.set_colorkey(BLACK)
    explosionAnim['player'].append(img)

powerUpImages = {'shield': pygame.image.load(path.join(imgDir, 'shield_gold.png')).convert(),
                 'gun': pygame.image.load(path.join(imgDir, 'bolt_gold.png')).convert()}

shootingSound = pygame.mixer.Sound(path.join(soundDir, 'pew.wav'))
missileSound = pygame.mixer.Sound(path.join(soundDir, 'rocket.ogg'))
explSounds = []
for sound in ['expl3.wav', 'expl6.wav']:
    explSounds.append(pygame.mixer.Sound(path.join(soundDir, sound)))

pygame.mixer.music.set_volume(0.2)

playerDieSound = pygame.mixer.Sound(path.join(soundDir, 'rumble1.ogg'))


running = True
menuDisplay = True
while running:
    if menuDisplay:
        main()
        pygame.time.wait(3000)

        pygame.mixer.music.stop()

        pygame.mixer.music.load(path.join(soundDir, 'tgfcoder-FrozenJam-SeamlessLoop.ogg'))

        pygame.mixer.music.play(-1)

        menuDisplay = False

        allSprites = pygame.sprite.Group()
        player = Player()
        allSprites.add(player)

        mobs = pygame.sprite.Group()
        for i in range(8):
            newMob()

        bullets = pygame.sprite.Group()
        powerups = pygame.sprite.Group()

        score = 0

    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    allSprites.update()

    hits = pygame.sprite.groupcollide(mobs, bullets, True, True)

    for hit in hits:
        score += 50 - hit.radius
        random.choice(explSounds).play()
        expl = Explosion(hit.rect.center, 'lg')
        allSprites.add(expl)
        if random.random() > 0.9:
            pow = Pow(hit.rect.center)
            allSprites.add(pow)
            powerups.add(pow)
        newMob()

    hits = pygame.sprite.spritecollide(player, mobs, True, pygame.sprite.collide_circle)
    for hit in hits:
        player.shield -= hit.radius * 2
        expl = Explosion(hit.rect.center, 'sm')
        allSprites.add(expl)
        newMob()
        if player.shield <= 0:
            playerDieSound.play()
            deathExplosion = Explosion(player.rect.center, 'player')
            allSprites.add(deathExplosion)
            player.hide()
            player.lives -= 1
            player.shield = 100

    hits = pygame.sprite.spritecollide(player, powerups, True)
    for hit in hits:
        if hit.type == 'shiled':
            player.shield += random.randrange(10, 30)
            if player.shield >= 100:
                player.shield = 100
        if hit.type == 'gun':
            player.powerup()

    if player.lives == 0 and not deathExplosion.alive():
        running = False

    screen.fill(BLACK)
    screen.blit(background, backgroundRect)

    allSprites.draw(screen)

    drawText(screen, str(score), 18, WIDTH / 2, 10)
    drawShieldBar(screen, 5, 5, player.shield)
    drawLives(screen, WIDTH - 100, 5, player.lives, playerMiniImg)

    pygame.display.flip()

pygame.quit()


