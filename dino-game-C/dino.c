/*
 * Dino Game in C (Windows console only)
 *
 * Controls:
 *   SPACE / W / Up arrow ... jump
 *   S / Down arrow ......... duck (on the ground) or fast-fall (in the air)
 *   X ...................... exit
 *
 * Score = distance travelled (one point per console column the world scrolls).
 *
 * Obstacles:
 *   cactus ........... jump over it
 *   low bird ......... jump over it
 *   mid-height bird .. duck under it (birds start appearing after BIRD_MIN_DIST)
 *
 * Ducking: console programs only see key presses, not key releases, so a
 * duck lasts DUCK_MS milliseconds and is extended while you hold the key
 * (keyboard auto-repeat). Jumping cancels a duck.
 *
 * The game needs a console window of at least 80 columns x 28 rows.
 *
 * Compile (MinGW / gcc on Windows):  gcc dino.c -o dino.exe
 * Compile (MSVC Developer prompt):   cl dino.c
 */
#include <conio.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <windows.h>

#define SCREEN_W        80
#define SCREEN_H        28
#define GROUND_Y        25   /* row of the ground line; sprites end on row 24 */
#define DINO_X          2
#define STAND_ROWS      10
#define DUCK_ROWS       5
#define JUMP_MAX        10   /* peak jump height in rows */
#ifndef JUMP_FRAMES
#define JUMP_FRAMES     24   /* frames in the air (parabolic arc with hang time) */
#endif
#define START_SPEED     40   /* ms per frame at the start */
#define MIN_SPEED       20   /* fastest ms per frame */
#define SPEEDUP_DIST    100  /* every this many columns the game gets 1 ms faster */
#define COLUMNS_PER_POINT 1  /* score = columns travelled / this */
#define DUCK_MS         1200
#define BIRD_MIN_DIST   300  /* birds appear after this many columns */
#define LOW_BIRD_Y      21   /* bird rows 21-22: jump over */
#define MID_BIRD_Y      17   /* bird rows 17-18: duck under */

enum { OB_CACTUS, OB_BIRD_LOW, OB_BIRD_MID };
enum { ACT_NONE, ACT_JUMP, ACT_DUCK, ACT_EXIT };

/* ---------------------------------------------------------------- sprites */

static const char *cactusArt[3] = {
    " # ",
    "###",
    " # ",
};

/* Birds fly left. Wings flap between the two frames. */
static const char *birdA[2] = { "  \\ /  ", "<(o)===" };
static const char *birdB[2] = { "<(o)===", "  / \\  " };

static const char *dinoBody[8] = {
    "        #####   ",
    "        ## ###  ",
    "        ######  ",
    "        ###     ",
    "  #    ####     ",
    "  ##  #####  #  ",
    "   ##########   ",
    "    ########    ",
};
static const char *legsA[2]   = { "     ##  ##     ", "     #    #     " };
static const char *legsB[2]   = { "     ##  ##     ", "     ##   #     " };
static const char *legsAir[2] = { "     ##  ##     ", "     ##  ##     " };

static const char *duckBody[4] = {
    "          #######",
    "          ## ####",
    "  ################",
    "   ##############",
};
static const char *duckLegsA = "     ##    #";
static const char *duckLegsB = "     #    ##";

/* ------------------------------------------------------------ game state */

typedef struct {
    int type, x, y, w, h;
} Obstacle;

typedef struct {
    int h;            /* height above the ground */
    int jumpT;        /* 0 on the ground, otherwise frames since take-off */
    int fastFall;     /* 1 while fast-falling after a Down press in the air */
    int ducking;
    DWORD duckUntil;  /* tick count until which the duck lasts */
    int frame;
    long distance;    /* columns travelled */
    int best;         /* best score this session */
    int speed;        /* ms per frame */
    Obstacle ob;
} Game;

static char cur[SCREEN_H][SCREEN_W];   /* the frame we want on screen */
static char prev[SCREEN_H][SCREEN_W];  /* what is on screen right now */
static unsigned char dinoMask[SCREEN_H][SCREEN_W];
static int originX = 0, originY = 0;   /* top-left of the visible console window */

static int scoreOf(const Game *g)
{
    return (int)(g->distance / COLUMNS_PER_POINT);
}

/* ------------------------------------------------------------ console I/O */

static void moveTo(int x, int y)
{
    COORD coord;
    coord.X = (SHORT)x;
    coord.Y = (SHORT)y;
    SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), coord);
}

static void setCursorVisible(int visible)
{
    CONSOLE_CURSOR_INFO info;
    info.dwSize = 1;
    info.bVisible = visible ? TRUE : FALSE;
    SetConsoleCursorInfo(GetStdHandle(STD_OUTPUT_HANDLE), &info);
}

/* Size and position of the visible console window. Returns 0 if unknown. */
static int windowInfo(int *cols, int *rows, int *left, int *top)
{
    CONSOLE_SCREEN_BUFFER_INFO info;
    if (!GetConsoleScreenBufferInfo(GetStdHandle(STD_OUTPUT_HANDLE), &info))
        return 0;
    *cols = info.srWindow.Right - info.srWindow.Left + 1;
    *rows = info.srWindow.Bottom - info.srWindow.Top + 1;
    *left = info.srWindow.Left;
    *top = info.srWindow.Top;
    return 1;
}

/* Write only the cells that changed since the last frame (no flicker).
 * Uses WriteConsoleOutputCharacterA, which writes straight to the console at
 * an absolute position, so it never depends on the cursor or on stdio buffering. */
static void flushFrame(void)
{
    HANDLE out = GetStdHandle(STD_OUTPUT_HANDLE);
    for (int y = 0; y < SCREEN_H; y++) {
        int x = 0;
        while (x < SCREEN_W) {
            if (cur[y][x] == prev[y][x]) {
                x++;
                continue;
            }
            int start = x;
            while (x < SCREEN_W && cur[y][x] != prev[y][x])
                x++;
            COORD at;
            DWORD written;
            at.X = (SHORT)(originX + start);
            at.Y = (SHORT)(originY + y);
            WriteConsoleOutputCharacterA(out, &cur[y][start], (DWORD)(x - start), at, &written);
        }
    }
    memcpy(prev, cur, sizeof cur);
}

/* Clears the screen and remembers where the visible window is. */
static void resetScreen(void)
{
    int cols, rows;
    system("cls");
    if (!windowInfo(&cols, &rows, &originX, &originY))
        originX = originY = 0;
    memset(prev, ' ', sizeof prev);
}

/* Makes sure the window is big enough. Returns 0 if the player quits instead. */
static int ensureWindowSize(void)
{
    int cols, rows, left, top;
    while (windowInfo(&cols, &rows, &left, &top) && (cols < SCREEN_W || rows < SCREEN_H)) {
        system("cls");
        printf("Console window is too small for the game.\n");
        printf("Needed: %d columns x %d rows.   Current: %d x %d.\n\n", SCREEN_W, SCREEN_H, cols, rows);
        printf("Enlarge or maximize the window (or run this in a separate\n");
        printf("cmd / PowerShell window), then press any key.  X = quit.\n");
        int k = _getch();
        if (k == 'x' || k == 'X')
            return 0;
        system("mode con: lines=29 cols=82");
    }
    return 1;
}

/* --------------------------------------------------------------- drawing */

static void put(int x, int y, char c)
{
    if (x >= 0 && x < SCREEN_W && y >= 0 && y < SCREEN_H)
        cur[y][x] = c;
}

static void putText(int x, int y, const char *fmt, ...)
{
    char buf[SCREEN_W + 1];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof buf, fmt, ap);
    va_end(ap);
    for (int i = 0; buf[i]; i++)
        put(x + i, y, buf[i]);
}

/* Draw a sprite (spaces are transparent).
 * isDino = 1: also records which cells the dino covers.
 * isDino = 0: returns 1 if any drawn cell overlaps the dino. */
static int stamp(int x, int y, const char *const *rows, int n, int isDino)
{
    int hit = 0;
    for (int r = 0; r < n; r++) {
        for (int c = 0; rows[r][c]; c++) {
            if (rows[r][c] == ' ')
                continue;
            int px = x + c, py = y + r;
            if (px < 0 || px >= SCREEN_W || py < 0 || py >= SCREEN_H)
                continue;
            cur[py][px] = rows[r][c];
            if (isDino)
                dinoMask[py][px] = 1;
            else if (dinoMask[py][px])
                hit = 1;
        }
    }
    return hit;
}

static int dinoRows(const Game *g, const char *rows[STAND_ROWS], int *top)
{
    int n;
    int legFrame = (g->frame >> 1) & 1;
    if (g->ducking) {
        for (n = 0; n < 4; n++)
            rows[n] = duckBody[n];
        rows[n++] = legFrame ? duckLegsB : duckLegsA;
        *top = GROUND_Y - DUCK_ROWS;
    } else {
        const char *const *legs = g->h > 0 ? legsAir : (legFrame ? legsB : legsA);
        for (n = 0; n < 8; n++)
            rows[n] = dinoBody[n];
        rows[n++] = legs[0];
        rows[n++] = legs[1];
        *top = GROUND_Y - STAND_ROWS - g->h;
    }
    return n;
}

/* Build the whole frame in `cur`. Returns 1 if the dino hits the obstacle. */
static int composeFrame(const Game *g)
{
    const char *rows[STAND_ROWS];
    int top, n;
    int score = scoreOf(g);

    memset(cur, ' ', sizeof cur);
    memset(dinoMask, 0, sizeof dinoMask);

    putText(10, 2, "X: Exit   SPACE/UP: Jump   S/DOWN: Duck");
    putText(62, 2, "SCORE : %d", score);
    putText(62, 3, "HI    : %d", g->best > score ? g->best : score);
    for (int x = 1; x < 80; x++)
        put(x, GROUND_Y, '=');

    n = dinoRows(g, rows, &top);
    stamp(DINO_X, top, rows, n, 1);

    const Obstacle *o = &g->ob;
    if (o->type == OB_CACTUS)
        return stamp(o->x, o->y, cactusArt, 3, 0);
    return stamp(o->x, o->y, ((g->frame >> 2) & 1) ? birdB : birdA, 2, 0);
}

/* ----------------------------------------------------------------- logic */

static void spawnObstacle(Game *g)
{
    Obstacle *o = &g->ob;
    memset(o, 0, sizeof *o);

    if (g->distance >= BIRD_MIN_DIST && rand() % 100 < 45) {
        o->type = (rand() % 2) ? OB_BIRD_MID : OB_BIRD_LOW;
        o->w = 7;
        o->h = 2;
        o->y = (o->type == OB_BIRD_MID) ? MID_BIRD_Y : LOW_BIRD_Y;
    } else {
        o->type = OB_CACTUS;
        o->w = 3;
        o->h = 3;
        o->y = GROUND_Y - 3;
    }
    o->x = SCREEN_W - 1 + rand() % 20; /* start just off-screen, random gap */
}

static void initGame(Game *g, int best)
{
    memset(g, 0, sizeof *g);
    g->best = best;
    g->speed = START_SPEED;
    spawnObstacle(g);
}

/* Parabolic jump: 0 at take-off and landing, JUMP_MAX at the midpoint. */
static int jumpHeight(int t)
{
    return (JUMP_MAX * 4 * t * (JUMP_FRAMES - t) + JUMP_FRAMES * JUMP_FRAMES / 2)
           / (JUMP_FRAMES * JUMP_FRAMES);
}

static void applyAction(Game *g, int action)
{
    if (action == ACT_JUMP) {
        if (g->jumpT == 0) {
            g->jumpT = 1;
            g->duckUntil = 0; /* jumping cancels a duck */
        }
    } else if (action == ACT_DUCK) {
        if (g->jumpT == 0) {
            g->duckUntil = GetTickCount() + DUCK_MS;
        } else {
            /* in the air: switch to the falling half of the arc and drop fast */
            if (g->jumpT < JUMP_FRAMES / 2)
                g->jumpT = JUMP_FRAMES - g->jumpT;
            g->fastFall = 1;
        }
    }
}

static void updatePlayer(Game *g)
{
    if (g->jumpT > 0) {
        g->jumpT += g->fastFall ? 2 : 1;
        if (g->jumpT >= JUMP_FRAMES) {
            g->jumpT = 0;
            g->fastFall = 0;
            g->h = 0;
        } else {
            g->h = jumpHeight(g->jumpT);
        }
    }
    g->ducking = (g->jumpT == 0 && (long)(g->duckUntil - GetTickCount()) > 0);
}

/* Advance one frame (no console output). Returns 1 on collision. */
static int tick(Game *g)
{
    g->frame++;
    g->distance++;           /* the world scrolls one column per frame */
    updatePlayer(g);
    g->ob.x--;

    int hit = composeFrame(g);

    g->speed = START_SPEED - (int)(g->distance / SPEEDUP_DIST);
    if (g->speed < MIN_SPEED)
        g->speed = MIN_SPEED;

    if (g->ob.x + g->ob.w < 0)
        spawnObstacle(g);
    return hit;
}

/* Reads every pending key. Returns ACT_EXIT if the player wants to quit. */
static int readInput(Game *g)
{
    while (_kbhit()) {
        int key = _getch();
        int action = ACT_NONE;

        if (key == 0 || key == 224) { /* arrow keys come as two codes */
            key = _getch();
            if (key == 72)
                action = ACT_JUMP;
            else if (key == 80)
                action = ACT_DUCK;
        } else if (key == ' ' || key == 'w' || key == 'W') {
            action = ACT_JUMP;
        } else if (key == 's' || key == 'S') {
            action = ACT_DUCK;
        } else if (key == 'x' || key == 'X') {
            return ACT_EXIT;
        }
        applyAction(g, action);
    }
    return ACT_NONE;
}

int main(void)
{
    int best = 0, running = 1;

    srand((unsigned)time(NULL));
    system("mode con: lines=29 cols=82");
    if (!ensureWindowSize())
        return 0;
    setCursorVisible(0);

    while (running) {
        Game g;
        initGame(&g, best);
        resetScreen();

        while (1) {
            if (readInput(&g) == ACT_EXIT) {
                running = 0;
                break;
            }

            if (tick(&g)) {
                int score = scoreOf(&g);
                if (score > best)
                    best = score;
                putText(32, 8, "GAME OVER - Score: %d", score);
                putText(26, 10, "Press any key to play again, X to exit");
                flushFrame();

                Sleep(400);
                while (_kbhit())
                    _getch(); /* drop keys held down during the crash */
                int k = _getch();
                if (k == 'x' || k == 'X')
                    running = 0;
                break;
            }

            flushFrame();
            Sleep((DWORD)g.speed);
        }
    }

    setCursorVisible(1);
    moveTo(0, SCREEN_H - 1);
    return 0;
}