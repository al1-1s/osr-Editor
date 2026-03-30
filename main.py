from core import unpack_osr
import tkinter as tk
from tkinter import filedialog
import json
import os
from datetime import datetime
from utils.replay import Replay

def select_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Choose osu! replay file", 
                                           filetypes=[("osr files", "*.osr"), ("All files", "*.*")])
    root.update_idletasks()
    root.destroy()
    return file_path if file_path else None

def main():
    working_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = select_file()
    
    if not file_path:
        print("No file selected.")
        return
    with open(file_path, "rb") as f:
        data = f.read()
        
    meta, life_bar_graph, replay_data = unpack_osr(data)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(working_dir, f"output_{ts}")
    os.makedirs(output_dir)
    
    meta_path = os.path.join(output_dir, "meta.json")
    life_bar_graph_path = os.path.join(output_dir, "life_bar_graph.txt")
    replay_data_path = os.path.join(output_dir, "replay_data.txt")
    
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4)
    with open(life_bar_graph_path, "w", encoding="utf-8") as f:
        f.write(life_bar_graph)
    with open(replay_data_path, "w", encoding="utf-8") as f:
        f.write(replay_data)
        
    print(f"Data extracted to: {output_dir}")

if __name__ == "__main__":
    main()
    # replay = Replay()
    # replay.load_from_file(r"C:\Users\Cre\Desktop\osuReplayReader\Arisu Tendou.osr")
    # print(replay)
    # print(dir(replay))
    
