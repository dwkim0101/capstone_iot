class Board(object):
    def __init__(self, board_name: str, pid: str, sn: str, vid: str, port_address: str):
        self.port_path = port_address
        self.vid = vid
        self.pid = pid
        self.board_name = board_name
        self.serial_number = sn

    def __str__(self) -> str:
        return f"<Board Obj: {self.port_path} | {self.serial_number} | {self.board_name}>"
    
    def __repr__(self) -> str:
        return f"<Board Obj @ {self.port_path}>"