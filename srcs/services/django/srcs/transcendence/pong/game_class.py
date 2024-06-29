import time, asyncio, uuid
from .constants import Costants
from channels.layers import get_channel_layer

class State:
    ...

class Vector2D:
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def normalizeVector(self):
        ...

class Ball:
    def __init__(self) -> None:
        self.position = Vector2D(0, 0)
        self.direction = Vector2D(1, 0)
        self.speed = Costants.BALL_SPEED

    def reset(self):
        self.position = Vector2D(0, 0)
        self.direction.y = 0
        self.speed = Costants.BALL_SPEED

    def check_limit_y(self):
        if self.position.y > Costants.MAX_PADDLE_Y \
            or self.position.y < Costants.MIN_PADDLE_Y :
            return True
        return False

    def check_limit_x(self):
        if self.position.x > Costants.MAX_WIDTH \
        or self.position.x < Costants.MIN_WIDTH:
            return True
        return False

    def update(self):
        self.position.x += self.speed * self.direction.x
        self.position.y += self.speed * self.direction.y


class Player:
    def __init__(self, name : str, vector : Vector2D) -> None:
        self.name : str = name
        self.position : Vector2D = vector
        self.speed = 1
        self.size = Costants.PADDLE_SIZE
        self.half_size = self.size / 2

        self.consumer = None

    def reset(self):
        self.position.y = 0
        self.speed = Costants.MOVSPEED

        # Reset powerups
        ...

    def set_consumer(self, consumer):
        self.consumer = consumer

    def ball_collision(self, ball : Ball):
        if ball.position.y <= self.position.y + self.half_size \
            and ball.position.y >= self.position.y - self.half_size:
            return True
        return False

class Match:

    def __init__(self) -> None:
        self.id = str(uuid.uuid4())
        self.player1 : Player = Player(str(uuid.uuid4()) ,Vector2D(Costants.MIN_WIDTH, 0))
        self.player2 : Player = Player(str(uuid.uuid4()), Vector2D(Costants.MAX_WIDTH, 0))
        self.ball : Ball = Ball()
        self.score1 = 0
        self.score2 = 0
        self.channel_layer = get_channel_layer()
        self.started = False
        self.ended = False
        self.full = False
        self.event_update = False
        self.start_time = time.time()
        self.update_time = time.time()
        self.exchanges : int = 0
        self.task = None
        self.state = {
            "player_one": {"x": self.player1.position.x, "y": self.player1.position.y, "score": self.score1,},
            "player_two": {"x": self.player2.position.x, "y": self.player2.position.y, "score": self.score2,},
            "ball": {"x": self.ball.position.x, "y": self.ball.position.y,"dirX": self.ball.direction.x, "dirY": self.ball.direction.y, "speed": self.ball.speed,},
        }

    def set_task(self, task):
        self.task = task

    def which_player(self, consumer):
        if consumer == self.player1.consumer:
            return "player_one"
        elif consumer == self.player2.consumer:
            return "player_two"
        else:
            return "consumer_not_found"

    def get_consumer_players(self):
        return [self.player1.consumer, self.player2.consumer]

    async def send_to_channel(self, type: str, message: object):
        await self.channel_layer.group_send(
            self.id, {
                'type' : type,
                'message' : message
            }
        )

    def update_state(self):
        self.state['player_one']['x'] = self.player1.position.x
        self.state['player_one']['y'] = self.player1.position.y
        self.state['player_one']['score'] = self.score1
        self.state['player_two']['x'] = self.player2.position.x
        self.state['player_two']['y'] = self.player2.position.y
        self.state['player_two']['score'] = self.score2
        self.state['ball']['x'] = self.ball.position.x
        self.state['ball']['y'] = self.ball.position.y
        self.state['ball']['dirX'] = self.ball.direction.x
        self.state['ball']['dirY'] = self.ball.direction.y
        self.state['ball']['speed'] = self.ball.speed



    async def send_game_state(self):

        await self.channel_layer.group_send(self.id, {
            "type" : "game_message",
            "event" : "state",
            # "message" : self.state,
            'message' : {
                "player_one": {"x": self.player1.position.x, "y": self.player1.position.y, "score": self.score1,},
                "player_two": {"x": self.player2.position.x, "y": self.player2.position.y, "score": self.score2,},
                "ball": {"x": self.ball.position.x, "y": self.ball.position.y,"dirX": self.ball.direction.x, "dirY": self.ball.direction.y, "speed": self.ball.speed,},
            }
        })

    def is_empty(self):
        if not self.player1 and not self.player2:
            return True
        return False

    def is_full(self):
        return self.full

    def is_ended(self) -> bool:
        return self.ended

    def is_started(self) -> bool:
        return self.started

    def add_player(self, consumer):
        if self.is_started():
            return
        if not self.player1.consumer:
            self.player1.consumer = consumer
        elif not self.player2.consumer:
            self.player2.consumer = consumer
        if self.player1.consumer and self.player2.consumer:
            self.full = True

    def start_match(self):
        if self.player1.consumer and self.player2.consumer:
            self.started = True

    async def end_match(self):
        if self.task:
            asyncio.cancel(self.task)
            self.task = None
        self.ended = True
        self.player1 = None
        self.player2 = None

    def check_players(self):
        if not self.player1.consumer or not self.player2.consumer:
            return False
        return True

    async def check_powerup(self):
        ...

    def handle_powerup():
        ...

    async def handle_player_collision(self, player : Player):

        if player.ball_collision(self.ball):
            self.event_update = True
            self.ball.direction.y = (self.ball.position.y - player.position.y) / 10
            self.ball.direction.x *= -1
            self.ball.position.x = player.position.x

            self.exchanges += 1

            # Send exchanges

    async def ball_player_collision(self):
        if self.event_update:
            return

        if self.ball.check_limit_x():
            if self.ball.direction.x > 0:
                await self.handle_player_collision(self.player2)
            elif self.ball.direction.x < 0:
                await self.handle_player_collision(self.player1)
            # print('funcion called')
            # player1 = self.player1.ball_collision(self.ball)
            # player2 = self.player2.ball_collision(self.ball)
            # print(player1)
            # print(player2)
            # if player1 or player2:
            #     self.event_update = True
            #     if player1:
            #         self.handle_player_collision(player1)
            #     elif player2:
            #         self.handle_player_collision(player2)
            # else:
            #     print('no player')

    async def wall_collision(self):
        if self.event_update:
            return
        if self.ball.check_limit_y():
            self.event_update = True
            limit = Costants.MAX_PADDLE_Y if self.ball.position.y > Costants.MAX_PADDLE_Y else Costants.MIN_PADDLE_Y
            self.ball.direction.y *= -1
            self.ball.position.y = limit

    async def check_point(self):
        if self.event_update:
            return
        if self.ball.check_limit_x():
            self.event_update = True
            scorer = self.player1 if self.ball.position.x > 0 else self.player2
            if scorer == self.player1:
                self.score1 += 1
            else:
                self.score2 += 1

            self.exchanges = 0
            self.player1.reset()
            self.player2.reset()
            self.ball.reset()

            # Send score
            await self.channel_layer.group_send("game_message", {
                "event" : "score",
                "message" : {
                    "player_one": self.score1,
                    "player_two": self.score2
                }
            })

            # Check game ended
            if self.score1 == Costants.MAX_SCORE or self.score2 == Costants.MAX_SCORE:
                self.ended = True

    def move(self, consumer, direction):
        player: Player = None
        if self.player1.consumer == consumer:
            player = self.player1
        elif self.player2.consumer == consumer:
            player = self.player2
        if not player:
            return

        if direction == 'up':
            player.position.y += player.speed
        elif direction == 'down':
            player.position.y -= player.speed

    async def update(self):
        now = time.time()
        if now - self.update_time < Costants.REFRESH_RATE:
            await asyncio.sleep(Costants.REFRESH_RATE - ( now - self.update_time))

        self.ball.update()

        self.event_update = False

        await self.ball_player_collision()

        await self.check_point()

        await self.wall_collision()

        self.update_state()

        self.update_time = time.time()
