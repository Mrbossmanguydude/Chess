import pygame
import copy
from os.path import join

pygame.init()

WIDTH, HEIGHT = 800, 800
SQUARE_SIZE = 100
screen = pygame.display.set_mode((WIDTH, HEIGHT))

def flip(sprites):
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

def spritesheet(dir1, filename, width, height, y, direction=False):
    path = join("images", dir1, filename)

    all_sprites = {}

    sprite_sheet = pygame.image.load(path).convert_alpha()
    sprites = []
    for i in range(sprite_sheet.get_width() // width):
        surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
        rect = pygame.Rect(i * width, y, width, height)
        surface.blit(sprite_sheet, (0,0), rect)
        sprites.append(pygame.transform.scale2x(surface))
    if direction:
        all_sprites[filename.replace(".png", "") + "_right"] = sprites 
        all_sprites[filename.replace(".png", "") + "_left"] = flip(sprites)
    else:
        all_sprites[filename.replace(".png", "")] = sprites
    return all_sprites

white_pieces = spritesheet("Chess_pieces", "Chess_Peices.png", 161, 155, 0)
black_pieces = spritesheet("Chess_pieces", "Chess_Peices.png", 161, 155, 155)

chess_pieces = {
    "wking" : [None, (8, 0)],
    "wqueen" : [None, (2, 0)],
    "wbishop" : [None, (0, 0)],
    "wknight" : [None, (-5, 0)],
    "wrook" : [None, (-13, 0)],
    "wpawn" : [None, (-20, 0)],
    "bking" : [None, (8, 0)],
    "bqueen" : [None, (2, 0)],
    "bbishop" : [None, (0, 0)],
    "bknight" : [None, (-5, 0)],
    "brook" : [None, (-13, 0)],
    "bpawn" : [None, (-20, 0)]
}

pieces_order = ["king", "queen", "bishop", "knight", "rook", "pawn"]
for i, piece in enumerate(pieces_order):
    chess_pieces["w" + piece][0] = white_pieces["Chess_Peices"][i]
    chess_pieces["b" + piece][0] = black_pieces["Chess_Peices"][i]

board = [[0 for _ in range(8)] for _ in range(8)]

def draw_board(screen, chess_pieces, board):
    block_size = 100  
    for x in range(0, WIDTH, block_size):
        for y in range(0, HEIGHT, block_size):
            if (x//block_size-y//block_size) % 2 == 0:
                pygame.draw.rect(screen, (125, 135, 150), pygame.Rect(x, y, block_size, block_size))
            else:
                pygame.draw.rect(screen, (233, 236, 239), pygame.Rect(x, y, block_size, block_size))

    for i in board:
        screen.blit(pygame.transform.scale(chess_pieces[board[i]][0].convert_alpha(), (100, 100)), (i[0]*100 + chess_pieces[board[i]][1][0], i[1]*100 + chess_pieces[board[i]][1][1]))

def fen_decoder(fen, player_side):
    fen_parts = fen.split(' ')
    board = {}
    rows = fen_parts[0].split('/')
    
    piece_names = {
        'p': 'bpawn',
        'r': 'brook',
        'n': 'bknight',
        'b': 'bbishop',
        'q': 'bqueen',
        'k': 'bking',
        'P': 'wpawn',
        'R': 'wrook',
        'N': 'wknight',
        'B': 'wbishop',
        'Q': 'wqueen',
        'K': 'wking'
    }
    
    for i, row in enumerate(rows):
        col = 0
        for char in row:
            if char.isdigit():
                col += int(char)
            else:
                board[(col, i if player_side == "w" else 7-i)] = piece_names[char]
                col += 1
    castling_availability = fen_parts[2]
    en_passant_target_square = fen_parts[3]
    halfmove_clock = int(fen_parts[4])
    fullmove_number = int(fen_parts[5])
    
    return {
        'board': board,
        'castling_availability': castling_availability,
        'en_passant_target_square': en_passant_target_square,
        'halfmove_clock': halfmove_clock,
        'fullmove_number': fullmove_number,
    }

def get_attacked_squares(piece_objects, board, en_passant_square, white_attacked_squares, black_attacked_squares) -> list:
    white_attacked_squares = []
    black_attacked_squares = []
    for piece in piece_objects:
        
        if isinstance(piece, Pawn):
            piece.check_legal_moves(board, en_passant_square)
            if piece.color == "w":
                white_attacked_squares.extend(piece.attacked_squares)

            else:
                black_attacked_squares.extend(piece.attacked_squares)

        elif isinstance(piece, King):
            piece.check_legal_moves(board, piece_objects, white_attacked_squares, black_attacked_squares)

        else:
            piece.check_legal_moves(board)
            if piece.color == "w":
                white_attacked_squares.extend(piece.legal_moves)

            else:
                black_attacked_squares.extend(piece.legal_moves)

    return white_attacked_squares, black_attacked_squares

def get_pieces(board, en_passant_square, castling_availability, white_attacked_squares, black_attacked_squares) -> list:
    piece_objects = []
    for piece in board:
        piece_type = board[piece][1:]
        piece_color = board[piece][0]
        if piece_type == "pawn":
            piece_objects.append(Pawn(piece_color, piece))
        elif piece_type == "king":
            piece_objects.append(King(piece_color, piece, castling_availability))
        elif piece_type == "rook":
            piece_objects.append(Rook(piece_color, piece))
        elif piece_type == "bishop":
            piece_objects.append(Bishop(piece_color, piece))
        elif piece_type == "queen":
            piece_objects.append(Queen(piece_color, piece))
        elif piece_type == "knight":
            piece_objects.append(Knight(piece_color, piece))

    for piece in piece_objects:
        if not isinstance(piece, Pawn) and not isinstance(piece, King):
            piece.check_legal_moves(board)
        elif isinstance(piece, Pawn):
            piece.check_legal_moves(board, en_passant_square)
        elif isinstance(piece, King):
            piece.check_legal_moves(board, piece_objects, white_attacked_squares, black_attacked_squares)
    return piece_objects

class Pawn:
    def __init__(self, color, position):
        self.color = color
        self.position = position
        self.has_moved = False if (self.position[1] == 6 and color == "w") or (self.position[1] == 1 and color == "b") else True
        self.promotion_pieces = [color+"bishop", color+"knight", color+"rook", color+"queen"]
        self.possible_vectors = [(0, -1), (-1, -1), (1, -1), (0, -2)] if color == "w" else [(0, 1), (-1, 1), (1, 1), (0, 2)] 
        self.legal_moves = []
        self.attacked_squares = []
    
    def check_legal_moves(self, board, en_passant_square) -> None:
        self.legal_moves = []
        move_over = {-2 : -1, 2 : 1, -1 : -1, 1 : 1}
        self.attacked_squares, self.legal_moves = [], []
        for vector in self.possible_vectors:
            if self.position[0] + vector[0] < 8 and self.position[0] + vector[0] >= 0 and self.position[1] + vector[1] < 8 and self.position[1] + vector[1] >= 0:
                if (self.position[0] + vector[0], self.position[1] + vector[1]) in board and vector in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                    self.legal_moves.append((self.position[0] + vector[0], self.position[1] + vector[1]))

                elif (self.position[0] + vector[0], self.position[1] + vector[1]) not in board and vector in [(-1, -1), (1, -1), (-1, 1), (1, 1)] and (self.position[0] + vector[0], self.position[1] + vector[1]) == en_passant_square:
                    self.legal_moves.append((self.position[0] + vector[0], self.position[1] + vector[1]))

                elif (self.position[0] + vector[0], self.position[1] + vector[1]) not in board and vector in [(0, 1), (0, -1)]:
                    self.legal_moves.append((self.position[0] + vector[0], self.position[1] + vector[1]))
                
                elif ((self.position[0] + vector[0], self.position[1] + vector[1]) not in board and (self.position[0], self.position[1] + move_over[vector[1]]) not in board) and vector in [(0, 2), (0, -2)] and not self.has_moved:
                    self.legal_moves.append((self.position[0] + vector[0], self.position[1] + vector[1]))

                if vector in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
                    if (self.position[0] + vector[0], self.position[1] + vector[1]) in board:
                        if board[(self.position[0] + vector[0], self.position[1] + vector[1])][0] != self.color:
                            self.attacked_squares.append((self.position[0] + vector[0], self.position[1] + vector[1]))
                    else:
                        self.attacked_squares.append((self.position[0] + vector[0], self.position[1] + vector[1]))
class King:
    def __init__(self, color, position, castling_availability):
        self.color = color
        self.position = position
        self.possible_vectors = [(0, -1), (0, 1), (1, 0), (-1, 0), (1, 1), (-1, 1), (-1, -1), (1, -1)]
        self.has_moved = False
        self.legal_moves = []

    def check_legal_moves(self, board, piece_objects, white_attacked_squares, black_attacked_squares):
        self.legal_moves = []
        for vector in self.possible_vectors:
            next_pos = (self.position[0] + vector[0], self.position[1] + vector[1])
            if 0 <= next_pos[0] <= 8 and 0 <= next_pos[1] <= 8:
                if next_pos in board:
                    if board[next_pos][0] != self.color and board[next_pos][1:] != "king":
                        self.legal_moves.append(next_pos)
                else:
                    self.legal_moves.append(next_pos)

        rooks = {"w" : ["wrook", (7, 7), (0, 7)], "b" : ["brook", (7, 0), (0, 0)]}
        castle_moves = {"w" : {0 : (2, 0), 1 : (-2, 0)}, "b" : {0 : (2, 0), 1 : (-2, 0)}}
        empty_squares = {"w" : {0 : [(5, 7), (6, 7)], 1 : [(1, 7), (2, 7), (3, 7)]}, "b" : {0 : [(5, 0), (6, 0)], 1 : [(1, 0), (2, 0), (3, 0)]}}

        for color in rooks:
            for rook_pos in [rooks[color][1], rooks[color][2]]:
                if rook_pos in board and board[rook_pos] == rooks[color][0]:
                    rook = None
                    for piece in piece_objects:
                        if piece.position == rook_pos and isinstance(piece, Rook):
                            rook = piece

                    if rook != None:
                        if not rook.has_moved and not self.has_moved:
                            white_attacked_squares, black_attacked_squares
                            castle_elegibility = True
                            for i in empty_squares[color][rooks[color].index(rook_pos) - 1]:
                                if (color == "w" and i in black_attacked_squares) or (color == "b" and i in white_attacked_squares):
                                    castle_elegibility = False

                            if castle_elegibility:
                                new_position = (self.position[0] + castle_moves[color][rooks[color].index(rook_pos) - 1][0], self.position[1])
                                self.legal_moves.append(new_position)
                
class Piece_Long_Range:
    def __init__(self, color, position) -> None:
        self.color = color
        self.position = position
        self.vector_cols = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        self.vector_diagonals = [(1, 1), (-1, 1), (-1, -1), (1, -1)]
        self.legal_moves = []

    def check_cols(self, board):
        for direction in self.vector_cols:
            next_position = tuple(map(sum, zip(self.position, direction)))
            while 0 <= next_position[0] < 8 and 0 <= next_position[1] < 8:
                if next_position in board:
                    if board[next_position][0] != self.color:
                        self.legal_moves.append(next_position)
                    break 
                else:
                    self.legal_moves.append(next_position)

                next_position = tuple(map(sum, zip(next_position, direction)))

        return self.legal_moves

    def check_diagonals(self, board):
        for direction in self.vector_diagonals:
            next_position = tuple(map(sum, zip(self.position, direction)))
            while 0 <= next_position[0] < 8 and 0 <= next_position[1] < 8:
                if next_position in board:
                    if board[next_position][0] != self.color:
                        self.legal_moves.append(next_position)
                    break 
                else:
                    self.legal_moves.append(next_position)

                next_position = tuple(map(sum, zip(next_position, direction)))

        return self.legal_moves

class Rook(Piece_Long_Range):
    def __init__(self, color, position):
        super().__init__(color, position)
        self.has_moved = False

    def check_legal_moves(self, board):
        self.legal_moves = []
        self.check_cols(board)

class Bishop(Piece_Long_Range):
    def __init__(self, color, position):
        super().__init__(color, position)

    def check_legal_moves(self, board):
        self.legal_moves = []
        self.check_diagonals(board)

class Knight:
    def __init__(self, color, position):
        self.color = color
        self.position = position
        self.possible_vectors = [(-1, -2), (1, -2), (-2, -1), (2, -1), (-1, 2), (1, 2), (-2, 1), (2, 1)]
        self.legal_moves = []
        self.value = 3

    def check_legal_moves(self, board):
        self.legal_moves = []
        for vector in self.possible_vectors:
            new_pos = (self.position[0] + vector[0], self.position[1] + vector[1])
            if 0 <= new_pos[0] <= 7 and 0 <= new_pos[1] <= 7:
                if new_pos in board:
                    if board[new_pos][0] == self.color:
                        continue
                    else:
                        self.legal_moves.append(new_pos)
                else:
                    self.legal_moves.append(new_pos)

class Queen(Piece_Long_Range):
    def __init__(self, color, position):
        super().__init__(color, position)

    def check_legal_moves(self, board):
        self.legal_moves = []
        self.legal_moves.extend(self.check_cols(board))
        self.legal_moves.extend(self.check_diagonals(board))
        return self.legal_moves

def draw_highlighted_rect(surface, rect, border_color, highlight_color, border_thickness, highlight_thickness):
    pygame.draw.rect(surface, border_color, rect, border_thickness)
    inner_rect = pygame.Rect(rect.left + border_thickness, rect.top + border_thickness,rect.width - 2 * border_thickness, rect.height - 2 * border_thickness)
    pygame.draw.rect(surface, highlight_color, inner_rect, highlight_thickness)

def check_next_move(board, piece_objects, board_pos, selected_square, en_passant_square, dragged_info, white_attacked_squares, black_attacked_squares):
    temp_board = copy.deepcopy(board)
    temp_piece_objects = copy.deepcopy(piece_objects)

    for piece in temp_piece_objects:
        if piece.position == selected_square:
            selected_piece = piece
            break

    temp_board[board_pos] = dragged_info[0]
    selected_piece.position = board_pos

    for piece in temp_piece_objects:
        if piece.position == board_pos and piece != selected_piece:
            temp_piece_objects.remove(piece)
            break

    temp_white_attacked_squares, temp_black_attacked_squares = get_attacked_squares(temp_piece_objects, temp_board, en_passant_square, white_attacked_squares, black_attacked_squares)

    for piece in temp_piece_objects:
        if isinstance(piece, King) and piece.color == dragged_info[0][0]:
            if (piece.color == 'w' and piece.position in temp_black_attacked_squares) or \
               (piece.color == 'b' and piece.position in temp_white_attacked_squares):
                return True

    return False

starting_pos = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
rooks = "r7/8/8/8/8/8/8/R7 w - - 0 1"
board_info = fen_decoder(starting_pos, "w")
board = board_info["board"]
white_attacked_squares, black_attacked_squares = [], []

piece_objects = get_pieces(board, board_info["en_passant_target_square"],  board_info["castling_availability"], white_attacked_squares, black_attacked_squares)

FPS = 60
running = True
clock = pygame.time.Clock()
selected_square = None
turn = "w"
pygame.display.set_caption(f"Chess, {turn} to move.")
border_color = (255, 255, 255)
highlight_color = (80, 80, 80)
border_thickness = 1
highlight_thickness = 5
en_passant_square = board_info["en_passant_target_square"]
castling_availability = board_info["castling_availability"]
board_pos = None
dragging = False
dragged_piece = None
pygame.mouse.set_visible(False)

while running:
    clock.tick(FPS)
    screen.fill((255, 255, 255))

    mouse_pos = pygame.mouse.get_pos()
    i, j = mouse_pos[0] // SQUARE_SIZE, mouse_pos[1] // SQUARE_SIZE

    if i <= 7 and j <= 7:
        rect = pygame.Rect(i*SQUARE_SIZE, j*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                board_pos = (mouse_pos[0]//SQUARE_SIZE, mouse_pos[1]//SQUARE_SIZE)

                if board_pos in board and board[board_pos][0] == turn and not dragging:
                    dragging = True
                    dragged_piece = board_pos
                    dragged_info = [board[dragged_piece], dragged_piece]
                    board.pop(dragged_piece)
                    selected_square = None

                if selected_square != None:
                    selected_square = None
                    selected_piece = None
                    
                else:
                    selected_square = board_pos

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and dragging:
                dragging = False
                board_pos = (mouse_pos[0]//SQUARE_SIZE, mouse_pos[1]//SQUARE_SIZE)

                if selected_square != None:
                    if selected_square == dragged_info[1] and selected_square != board_pos and dragged_info[0][0] == turn:
                        if not check_next_move(board, piece_objects, board_pos, selected_square, en_passant_square, dragged_info, white_attacked_squares, black_attacked_squares):
                            for piece in piece_objects:
                                if piece.position == selected_square:
                                    selected_piece = piece
                            if board_pos in selected_piece.legal_moves:
                                if board_pos in board:
                                    for piece in piece_objects:
                                        if piece.position == board_pos:
                                            piece_objects.remove(piece)
                                            break

                                if isinstance(selected_piece, Pawn):
                                    if (board_pos[0] - selected_square[0], board_pos[1] - selected_square[1]) in [(0, 2), (0, -2)]:
                                        en_passant_square = (board_pos[0], board_pos[1] - 1) if selected_piece.color == "b" else (board_pos[0], board_pos[1] + 1)

                                    elif en_passant_square != None:
                                        if (board_pos[0] - selected_square[0], board_pos[1] - selected_square[1]) in [(-1, -1), (1, -1), (-1, 1), (1, 1)] and board_pos == en_passant_square:
                                            en_passant_square = None
                                            if selected_piece.color == "w":
                                                board.pop((board_pos[0], board_pos[1] + 1))
                                            
                                            else:
                                                board.pop((board_pos[0], board_pos[1] - 1))
                                    board[board_pos] = dragged_info[1]
                                    piece = dragged_info[0]
                                    board[board_pos] = piece
                                    if piece_objects[piece_objects.index(selected_piece)].position in board:
                                        for i in piece_objects:
                                            if i.position == board_pos:
                                                remove_piece = i
                                                break
                                        piece_objects.remove(remove_piece)
                                    piece_objects[piece_objects.index(selected_piece)].position = board_pos
                                    piece_objects[piece_objects.index(selected_piece)].has_moved = True
                                    turn = "w" if turn == "b" else "b"
                                    pygame.display.set_caption(f"Chess, {turn} to move.")
                                    white_attacked_squares, black_attacked_squares = get_attacked_squares(piece_objects, board, en_passant_square, white_attacked_squares, black_attacked_squares)

                                elif isinstance(selected_piece, King):
                                    next_pos = (board_pos[0] - selected_square[0], board_pos[1] - selected_square[1])

                                    if next_pos in [(2, 0), (-2, 0)]:
                                        rooks = {"w" : ["wrook", (7, 7), (0, 7)], "b" : ["brook", (7, 0), (0, 0)]}
                                        castle_pos = {"w" : {0 : [(6, 7), (5, 7)], 1 : [(2, 7), (3, 7)]}, "b" : {0 : [(6, 0), (5, 0)], 1 : [(2, 0), (3, 0)]}}
                                        empty_squares = {"w" : {0 : [(5, 7), (6, 7)], 1 : [(1, 7), (2, 7), (3, 7)]}, "b" : {0 : [(5, 0), (6, 0)], 1 : [(1, 0), (2, 0), (3, 0)]}}
                                        for color in rooks:
                                            if color == turn:
                                                if rooks[color][1] in board and next_pos == (2, 0):
                                                    if board[rooks[color][1]] == rooks[color][0]:
                                                        for piece in piece_objects:
                                                            if piece.position == rooks[color][1] and isinstance(piece, Rook):
                                                                rook = piece
                                                        
                                                        if not rook.has_moved and not selected_piece.has_moved:
                                                            white_attacked_squares, black_attacked_squares = get_attacked_squares(piece_objects, board, en_passant_square, white_attacked_squares, black_attacked_squares)
                                                            castle_elegibility = True
                                                            for i in empty_squares[color][rooks[color].index(rooks[color][1]) - 1]:
                                                                if (color == "w" and i in black_attacked_squares) or (color == "b" and i in white_attacked_squares):
                                                                    castle_elegibility = False

                                                            if castle_elegibility:
                                                                board[castle_pos[color][rooks[color].index(rooks[color][1]) - 1][0]] = color + "king"
                                                                board[castle_pos[color][rooks[color].index(rooks[color][1]) - 1][1]] = color + "rook"

                                                                piece_objects[piece_objects.index(selected_piece)].position = castle_pos[color][rooks[color].index(rooks[color][1]) - 1][0]
                                                                piece_objects[piece_objects.index(rook)].position = castle_pos[color][rooks[color].index(rooks[color][1]) - 1][1]
                                                                piece_objects[piece_objects.index(selected_piece)].has_moved = True
                                                                piece_objects[piece_objects.index(rook)].has_moved = True
                                                                board.pop(rooks[color][1])

                                                                for piece in piece_objects:
                                                                    if piece.position == rooks[color][1] and isinstance(piece, Rook):
                                                                        piece_objects.remove(piece)
                                                                        break
                                                                en_passant_square = None
                                                                turn = "w" if turn == "b" else "b"
                                                                pygame.display.set_caption(f"Chess, {turn} to move.")

                                                elif rooks[color][2] in board and next_pos == (-2, 0):
                                                    if board[rooks[color][2]] == rooks[color][0]:
                                                            for piece in piece_objects:
                                                                if piece.position == rooks[color][2] and isinstance(piece, Rook):
                                                                    rook = piece
                                                            
                                                            if not rook.has_moved and not selected_piece.has_moved:
                                                                white_attacked_squares, black_attacked_squares = get_attacked_squares(piece_objects, board, en_passant_square, white_attacked_squares, black_attacked_squares)
                                                                castle_elegibility = True
                                                                for i in empty_squares[color][rooks[color].index(rooks[color][2]) - 1]:
                                                                    if (color == "w" and i in black_attacked_squares) or (color == "b" and i in white_attacked_squares):
                                                                        castle_elegibility = False

                                                                if castle_elegibility:
                                                                    board[castle_pos[color][rooks[color].index(rooks[color][2]) - 1][0]] = color + "king"
                                                                    board[castle_pos[color][rooks[color].index(rooks[color][2]) - 1][1]] = color + "rook"

                                                                    piece_objects[piece_objects.index(selected_piece)].position = castle_pos[color][rooks[color].index(rooks[color][2]) - 1][0]
                                                                    piece_objects[piece_objects.index(rook)].position = castle_pos[color][rooks[color].index(rooks[color][2]) - 1][1]
                                                                    piece_objects[piece_objects.index(selected_piece)].has_moved = True
                                                                    piece_objects[piece_objects.index(rook)].has_moved = True
                                                                    board.pop(rooks[color][2])

                                                                    for piece in piece_objects:
                                                                        if piece.position == rooks[color][2] and isinstance(piece, Rook):
                                                                            piece_objects.remove(piece)
                                                                            break
                                                                    en_passant_square = None
                                                                    turn = "w" if turn == "b" else "b"
                                                                    pygame.display.set_caption(f"Chess, {turn} to move.")

                                    else:
                                        board[board_pos] = dragged_info[1]
                                        piece = dragged_info[0]
                                        board[board_pos] = piece
                                        if piece_objects[piece_objects.index(selected_piece)].position in board:
                                            for i in piece_objects:
                                                if i.position == board_pos:
                                                    remove_piece = i
                                                    break
                                            piece_objects.remove(remove_piece)
                                        piece_objects[piece_objects.index(selected_piece)].position = board_pos
                                        piece_objects[piece_objects.index(selected_piece)].has_moved = True
                                        white_attacked_squares, black_attacked_squares = get_attacked_squares(piece_objects, board, en_passant_square, white_attacked_squares, black_attacked_squares)
                                        en_passant_square = None
                                        turn = "w" if turn == "b" else "b"
                                        pygame.display.set_caption(f"Chess, {turn} to move.")
                                                
                                else:
                                    board[board_pos] = dragged_info[1]
                                    piece = dragged_info[0]
                                    board[board_pos] = piece
                                    if piece_objects[piece_objects.index(selected_piece)].position in board:
                                        for i in piece_objects:
                                            if i.position == board_pos:
                                                remove_piece = i
                                                break
                                        piece_objects.remove(remove_piece)
                                    piece_objects[piece_objects.index(selected_piece)].position = board_pos
                                    piece_objects[piece_objects.index(selected_piece)].has_moved = True
                                    white_attacked_squares, black_attacked_squares = get_attacked_squares(piece_objects, board, en_passant_square, white_attacked_squares, black_attacked_squares)
                                    en_passant_square = None
                                    turn = "w" if turn == "b" else "b"
                                    pygame.display.set_caption(f"Chess, {turn} to move.")
                                

                            elif board_pos not in selected_piece.legal_moves:
                                board[dragged_info[1]] = dragged_info[0]

                        else:
                            board[dragged_info[1]] = dragged_info[0]

                    elif selected_square == board_pos:
                            board[dragged_info[1]] = dragged_info[0]

                    white_attacked_squares, black_attacked_squares = get_attacked_squares(piece_objects, board, en_passant_square, white_attacked_squares, black_attacked_squares)
                    selected_square = None
                    selected_piece = None

    draw_board(screen, chess_pieces, board)
    draw_highlighted_rect(screen, rect, border_color, highlight_color, border_thickness, highlight_thickness)
    if dragging:
        screen.blit(pygame.transform.scale(chess_pieces[dragged_info[0]][0], (100, 100)), (mouse_pos[0], mouse_pos[1]))

    pygame.display.flip()

pygame.quit()