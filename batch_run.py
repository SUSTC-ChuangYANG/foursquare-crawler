import subprocess
import multiprocessing
import time 
import argparse
import os 

def execute_command(command):
    start = time.time()
    print (f"Start: {command}")
    subprocess.run(command, shell=True)
    end = time.time()
    print(f"Finish: {command}, Totally: {round(end-start, 2)} seconds")

def worker(i, commands_queue):
    while True:
        command = commands_queue.get()
        if command is None:
            break
        execute_command(command)
        
    
def batch_runner(commands, pool_size):
    # 创建一个队列来存放命令
    commands_queue = multiprocessing.Queue()

    # 向队列中添加命令
    for command in commands:
        commands_queue.put(command)

    # 创建一个进程池
    pool = [multiprocessing.Process(target=worker, args= (i, commands_queue) ) for i in range(pool_size)]

    # 启动所有进程
    for p in pool:
        time.sleep(0.1) # 避免同时启动所有进程导致输出混乱
        p.start()

    # 发送None作为信号，告诉进程没有更多的命令需要执行
    for _ in range(len(pool)):
        commands_queue.put(None)

    # 等待所有进程完成
    for p in pool:
        p.join()

# you need to segment the full urls list into different files by yourself
def get_file_path_by_segment_number(indir, segment_number):
    return os.path.join(indir, f"url_segment_{segment_number}.csv")
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool_size", type=int, default=10)
    parser.add_argument("--indir", type=str, default="/home/chuang/foursquare-jp4/dataset/foursquare/raw_url/")
    parser.add_argument("--outdir", type=str, default="../../../dataset/foursquare/crawled_metadata/")
    parser.add_argument("--ip_pool", type=str, default="none", help="none or path to ip pool file, for large scale crawling, need to use ip pool to avoid being blocked by the website.")
    args = parser.parse_args()
    
    # config 
    min_segment_num = 0 # start from segment 0
    max_segment_num = 100 # end at segment 100
    segment_numbers = list(range(min_segment_num, max_segment_num))
    
    commands = []
    for segment_num in segment_numbers:
        file_path = get_file_path_by_segment_number(args.indir, segment_num)
        command = f"python fsq_crawler.py --file {file_path} --outdir {args.outdir} --ip_pool {args.ip_pool}"
        commands.append(command)
        
    batch_runner(commands, pool_size=args.pool_size)