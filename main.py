import curses
import random
from collections import deque

MAP_SIZE = 33
MINE_PROBABILITY = 0.05
TOTAL_CELLS = MAP_SIZE * MAP_SIZE
TOTAL_MINES = int((TOTAL_CELLS - 1) * MINE_PROBABILITY)
CENTER = MAP_SIZE // 2

class Cell:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.has_mine = False
        self.mine_deactivated = False
        self.is_safe = False
        self.is_orange = False
        self.is_discovered = False
        self.is_visible = False

    def get_neighbors(self, game):
        neighbors = []
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = self.x + dx, self.y + dy
                if 0 <= nx < MAP_SIZE and 0 <= ny < MAP_SIZE:
                    neighbors.append(game.grid[ny][nx])
        return neighbors

    def count_adjacent_mines(self, game):
        count = 0
        for neighbor in self.get_neighbors(game):
            if neighbor.has_mine and not neighbor.mine_deactivated:
                count += 1
        return count

    def has_adjacent_orange(self, game):
        for neighbor in self.get_neighbors(game):
            if neighbor.is_orange or (neighbor.has_mine and not neighbor.mine_deactivated):
                return True
        return False

class Game:
    def __init__(self):
        self.grid = [[Cell(x, y) for x in range(MAP_SIZE)] for y in range(MAP_SIZE)]
        self.player_x = CENTER
        self.player_y = CENTER
        self.lives = 3
        self.game_over = False
        self.won = False
        self.message = ""
        self.generate_map()

    def generate_map(self):
        self._create_safe_region()
        self._place_mines()
        self._mark_center_safe()
        self._update_discovered()
        self._update_visibility()

    def _create_safe_region(self):
        self.grid[CENTER][CENTER].is_safe = True
        
        queue = deque([(CENTER, CENTER)])
        visited = set()
        visited.add((CENTER, CENTER))
        
        target_size = int(TOTAL_CELLS * random.uniform(0.35, 0.45))
        
        while len(visited) < target_size:
            candidates = []
            for y, x in visited:
                for dy, dx in [(-1,0), (1,0), (0,-1), (0,1)]:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < MAP_SIZE and 0 <= nx < MAP_SIZE and (nx, ny) not in visited:
                        candidates.append((nx, ny))
            
            if not candidates:
                break
            
            new_cell = random.choice(candidates)
            visited.add(new_cell)
            self.grid[new_cell[1]][new_cell[0]].is_safe = True
            queue.append(new_cell)

    def _get_frontier(self):
        frontier = []
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                cell = self.grid[y][x]
                if cell.is_safe:
                    continue
                for dy, dx in [(-1,0), (1,0), (0,-1), (0,1)]:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < MAP_SIZE and 0 <= nx < MAP_SIZE:
                        if self.grid[ny][nx].is_safe:
                            frontier.append(cell)
                            break
        return frontier

    def _bfs_connected_safe_cells(self, start):
        visited = set()
        queue = deque([start])
        visited.add((start.x, start.y))
        
        while queue:
            cx, cy = queue.popleft()
            for dy, dx in [(-1,0), (1,0), (0,-1), (0,1)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < MAP_SIZE and 0 <= ny < MAP_SIZE:
                    cell = self.grid[ny][nx]
                    if cell.is_safe and (nx, ny) not in visited:
                        visited.add((nx, ny))
                        queue.append((nx, ny))
        
        return visited

    def _place_mines(self):
        mines_placed = 0
        attempts = 0
        max_attempts = 1000
        
        while mines_placed < TOTAL_MINES and attempts < max_attempts:
            attempts += 1
            frontier = self._get_frontier()
            
            if not frontier:
                break
            
            candidates = [c for c in frontier if not c.has_mine]
            if not candidates:
                break
            
            candidate = random.choice(candidates)
            
            safe_cells = self._bfs_connected_safe_cells(self.grid[CENTER][CENTER])
            
            candidate.has_mine = True
            new_safe_cells = self._bfs_connected_safe_cells(self.grid[CENTER][CENTER])
            
            if len(new_safe_cells) < len(safe_cells) * 0.5:
                candidate.has_mine = False
                continue
            
            mines_placed += 1
            self._update_orange_cells()

    def _update_orange_cells(self):
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                cell = self.grid[y][x]
                if cell.has_mine:
                    continue
                cell.is_orange = cell.has_adjacent_orange(self)

    def _mark_center_safe(self):
        center_cell = self.grid[CENTER][CENTER]
        center_cell.is_safe = True
        center_cell.is_discovered = True
        
        for cell in center_cell.get_neighbors(self):
            if cell.has_mine:
                continue
            if cell.has_adjacent_orange(self):
                cell.is_orange = True
            else:
                cell.is_safe = True

    def _flood_fill_discover(self, start_cell):
        queue = deque([start_cell])
        discovered = set()
        
        while queue:
            cell = queue.popleft()
            if (cell.x, cell.y) in discovered:
                continue
            if cell.has_mine:
                continue
            
            discovered.add((cell.x, cell.y))
            cell.is_discovered = True
            
            if cell.is_safe:
                for neighbor in cell.get_neighbors(self):
                    if neighbor.has_mine:
                        continue
                    if not neighbor.is_discovered and (neighbor.x, neighbor.y) not in discovered:
                        queue.append(neighbor)
            elif cell.is_orange:
                pass

    def _update_discovered(self):
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                cell = self.grid[y][x]
                if cell.is_safe and not cell.is_discovered:
                    self._flood_fill_discover(cell)

    def _update_visibility(self):
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                cell = self.grid[y][x]
                cell.is_visible = (abs(x - self.player_x) <= 5 and abs(y - self.player_y) <= 5)

    def move_player(self, dx, dy):
        new_x = self.player_x + dx
        new_y = self.player_y + dy
        
        if not (0 <= new_x < MAP_SIZE and 0 <= new_y < MAP_SIZE):
            return
        
        current_cell = self.grid[self.player_y][self.player_x]
        new_cell = self.grid[new_y][new_x]
        
        if new_cell.has_mine and not new_cell.mine_deactivated:
            self.reveal_all_mines()
            self.lives = 0
            self.game_over = True
            self.message = "¡Has pisado una mina! Juego terminado."
            return
        
        self.player_x = new_x
        self.player_y = new_y
        
        self._update_visibility()
        self._check_win()

    def deactivate_mine(self):
        cell = self.grid[self.player_y][self.player_x]
        
        if cell.has_mine:
            cell.mine_deactivated = True
            cell.is_safe = True
            self._update_orange_cells()
            self._update_discovered()
            self._check_win()
            self.message = "¡Mina desactivada!"
        else:
            self.lives -= 1
            self.message = f"¡No había mina! Te quedan {self.lives} vidas."
            if self.lives <= 0:
                self.game_over = True
                self.message = "¡Te has quedado sin vidas! Juego terminado."

    def use_radar(self):
        cell = self.grid[self.player_y][self.player_x]
        count = cell.count_adjacent_mines(self)
        
        notes = ['Do', 'Re', 'Mi', 'Fa', 'Sol']
        if count >= 5:
            note = 'Sol (5+)'
        else:
            note = notes[count]
        
        self.message = f"Radar: {count} mina(s) cerca - Nota: {note}"
        return count

    def reveal_all_mines(self):
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                cell = self.grid[y][x]
                if cell.has_mine and not cell.mine_deactivated:
                    cell.is_visible = True
                    cell.is_discovered = True

    def _check_win(self):
        mines_remaining = 0
        for y in range(MAP_SIZE):
            for x in range(MAP_SIZE):
                cell = self.grid[y][x]
                if cell.has_mine and not cell.mine_deactivated:
                    mines_remaining += 1
        
        if mines_remaining == 0:
            self.won = True
            self.game_over = True
            self.message = "¡Felicidades! Has desactivado todas las minas."

    def get_display_char(self, cell):
        if self.player_x == cell.x and self.player_y == cell.y:
            return '☺', curses.COLOR_CYAN
        
        if cell.has_mine and not cell.mine_deactivated:
            if cell.is_visible:
                return '✸', curses.COLOR_RED
            return '?', curses.COLOR_WHITE
        
        if cell.mine_deactivated:
            return '✓', curses.COLOR_RED
        
        if not cell.is_visible:
            return '░', curses.COLOR_BLACK
        
        if cell.is_safe:
            return ' ', curses.COLOR_WHITE
        elif cell.is_orange:
            return '▒', curses.COLOR_YELLOW
        
        return '░', curses.COLOR_BLACK

def draw_game(stdscr, game):
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    
    start_x = max(0, (width - MAP_SIZE * 2) // 2)
    start_y = max(1, (height - MAP_SIZE) // 2)
    
    title = "BUSCAMINAS RADAR"
    stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
    
    info = f"Vidas: {game.lives} | Posición: ({game.player_x}, {game.player_y})"
    stdscr.addstr(1, (width - len(info)) // 2, info)
    
    for y in range(MAP_SIZE):
        for x in range(MAP_SIZE):
            cell = game.grid[y][x]
            char, color = game.get_display_char(cell)
            
            display_x = start_x + x * 2
            display_y = start_y + y
            
            if 0 <= display_y < height - 1 and 0 <= display_x < width - 1:
                stdscr.addch(display_y, display_x, char, curses.color_pair(color) | curses.A_BOLD)
    
    if game.message:
        msg_y = start_y + MAP_SIZE + 1
        if msg_y < height - 1:
            stdscr.addstr(msg_y, 0, game.message, curses.A_REVERSE)
    
    controls = "Flechas: Mover | Q: Radar | W: Desactivar mina | R: Reiniciar | ESC: Salir"
    if height > start_y + MAP_SIZE + 3:
        stdscr.addstr(height - 1, 0, controls[:width-1])
    
    stdscr.refresh()

def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(curses.COLOR_BLACK, curses.COLOR_BLACK, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_WHITE, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_RED, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_GREEN, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_YELLOW, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_BLUE, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(curses.COLOR_CYAN, curses.COLOR_CYAN, curses.COLOR_BLACK)
    
    game = Game()
    
    while True:
        draw_game(stdscr, game)
        
        if game.game_over:
            if game.won:
                stdscr.addstr(curses.LINES // 2, curses.COLS // 2 - 10, "¡HAS GANADO!", curses.A_BOLD | curses.color_pair(curses.COLOR_GREEN))
            else:
                stdscr.addstr(curses.LINES // 2, curses.COLS // 2 - 10, "GAME OVER", curses.A_BOLD | curses.color_pair(curses.COLOR_RED))
            stdscr.refresh()
            curses.napause(2000)
            key = stdscr.getch()
            if key == ord('r') or key == ord('R'):
                game = Game()
                continue
            elif key == 27:
                break
            continue
        
        key = stdscr.getch()
        
        if key == curses.KEY_UP:
            game.move_player(0, -1)
        elif key == curses.KEY_DOWN:
            game.move_player(0, 1)
        elif key == curses.KEY_LEFT:
            game.move_player(-1, 0)
        elif key == curses.KEY_RIGHT:
            game.move_player(1, 0)
        elif key == ord('q') or key == ord('Q'):
            game.use_radar()
        elif key == ord('w') or key == ord('W'):
            game.deactivate_mine()
        elif key == ord('r') or key == ord('R'):
            game = Game()
        elif key == 27:
            break

if __name__ == "__main__":
    curses.wrapper(main)
