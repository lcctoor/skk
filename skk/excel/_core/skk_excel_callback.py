import shutil, socket, gc, subprocess
from datetime import datetime as datetime2
from pathlib import Path as lpath


excel_dir = lpath(__file__).parent.parent
ipynb_file = excel_dir / 'tutorial.ipynb'
xlsx_file = excel_dir / '2025年商品信息.xlsx'


def get_free_port() -> int:
    sock = socket.socket()
    sock.bind(('localhost', 0))
    port = sock.getsockname()[1]
    sock.close()
    del sock
    gc.collect()
    return port

def skk_excel_callback():
    run_dir = lpath.cwd()
    t = datetime2.now().strftime(r"_dev_%m%d_%H%M%S")
    ipynb_name = f"{t}.ipynb"
    shutil.copyfile(ipynb_file, run_dir / ipynb_name)
    shutil.copyfile(xlsx_file, run_dir / '2025年商品信息.xlsx')
    port = get_free_port()
    cmd_express = f"jupyter lab --port {port} {ipynb_name}"
    subprocess.run(cmd_express, shell=True, check=True)
